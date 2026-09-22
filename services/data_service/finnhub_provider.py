"""
ATHENA Finnhub Market Data & Financial Intelligence Provider
Integrates with Finnhub REST API (https://finnhub.io/api/v1) for real-time US quotes,
historical candlestick bars, fundamental metrics, and institutional news sentiment.
Includes strict 60 calls/min Token-Bucket sliding rate limiting and in-memory TTL caching.
"""

import asyncio
from collections import deque
from datetime import datetime, timedelta
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

from packages.common.config import settings
from packages.logging.logger import get_logger
from packages.schemas.market import Candle, OrderBookLevel, OrderBookSnapshot, Tick
from .providers import MockMarketDataProvider

logger = get_logger("athena.finnhub_data_provider")


class FinnhubMarketDataProvider(MockMarketDataProvider):
    """
    Direct interface to Finnhub Stock API v1.
    Provides real-time price quotes, historical OHLCV data, company financial metrics,
    and news sentiment streams.
    Protected by a 55 calls/min sliding window rate limiter and multi-tier TTL caches.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_requests_per_minute: Optional[int] = None,
    ):
        super().__init__()
        self.api_key = api_key if api_key is not None else (settings.FINNHUB_API_KEY or "")
        self.base_url = (base_url or settings.FINNHUB_BASE_URL or "https://finnhub.io/api/v1").rstrip("/")
        self.headers = {
            "X-Finnhub-Token": self.api_key,
            "Content-Type": "application/json",
        }
        self.max_requests_per_minute = (
            max_requests_per_minute
            if max_requests_per_minute is not None
            else getattr(settings, "FINNHUB_RATE_LIMIT_PER_MINUTE", 55)
        )

        # Sliding window rate limiter (tracks monotonic timestamps)
        self._request_timestamps: deque = deque()
        self._rate_lock = asyncio.Lock()

        # Multi-tier In-Memory TTL Caches: {symbol: (cached_at_monotonic, data)}
        self._fundamentals_cache: Dict[str, Tuple[float, Dict[str, float]]] = {}
        self._news_cache: Dict[str, Tuple[float, List[str]]] = {}
        self._sentiment_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._quote_cache: Dict[str, Tuple[float, Tick]] = {}
        self._ohlcv_cache: Dict[str, Tuple[float, List[Candle]]] = {}

    def _has_valid_credentials(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5 and not self.api_key.startswith("MOCK"))

    async def _acquire_rate_limit(self) -> None:
        """Enforces strict sliding-window rate limit (default: 55 requests / 60 seconds)."""
        async with self._rate_lock:
            now = time.monotonic()
            # Evict timestamps older than 60 seconds
            while self._request_timestamps and now - self._request_timestamps[0] >= 60.0:
                self._request_timestamps.popleft()

            # If capacity reached, throttle until oldest request rolls past the 60s window
            if len(self._request_timestamps) >= self.max_requests_per_minute:
                oldest = self._request_timestamps[0]
                wait_seconds = max(0.1, 60.0 - (now - oldest) + 0.1)
                logger.info(
                    f"Finnhub rate limit threshold approached ({len(self._request_timestamps)}/{self.max_requests_per_minute} req/min). "
                    f"Throttling for {wait_seconds:.2f}s..."
                )
                await asyncio.sleep(wait_seconds)
                now = time.monotonic()
                while self._request_timestamps and now - self._request_timestamps[0] >= 60.0:
                    self._request_timestamps.popleft()

            self._request_timestamps.append(time.monotonic())

    async def _get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0
    ) -> Optional[httpx.Response]:
        """Performs a rate-limited GET request with HTTP 429 retry backoff."""
        if not self._has_valid_credentials():
            return None

        p = params.copy() if params else {}
        p["token"] = self.api_key
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(2):
            await self._acquire_rate_limit()
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.get(url, params=p)
                    if res.status_code == 200:
                        return res
                    elif res.status_code == 429:
                        retry_after = float(res.headers.get("Retry-After", 2.0))
                        logger.warning(f"Finnhub HTTP 429 Too Many Requests on {endpoint}. Backing off for {retry_after:.1f}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.warning(f"Finnhub HTTP {res.status_code} for {endpoint}: {res.text[:100]}")
                        return None
            except Exception as e:
                logger.warning(f"Finnhub request error for {endpoint}: {e}")
                return None
        return None

    async def get_quotes(self, symbol: str) -> Tick:
        """Fetches real-time price quote from Finnhub /quote with 10s TTL cache."""
        sym = symbol.upper()
        now = time.monotonic()

        if sym in self._quote_cache:
            ts, cached_tick = self._quote_cache[sym]
            if now - ts < 10.0:
                return cached_tick

        if not self._has_valid_credentials():
            return await super().get_quotes(sym)

        res = await self._get("/quote", params={"symbol": sym})
        if res and res.status_code == 200:
            try:
                data = res.json()
                c = float(data.get("c", 0.0))  # Current price
                if c > 0:
                    h = float(data.get("h", c))
                    l = float(data.get("l", c))
                    o = float(data.get("o", c))
                    spread = round(c * 0.0003, 2)
                    tick = Tick(
                        symbol=sym,
                        timestamp=datetime.utcnow(),
                        price=c,
                        size=100.0,
                        bid=round(c - spread / 2.0, 2),
                        ask=round(c + spread / 2.0, 2),
                        bid_size=100.0,
                        ask_size=100.0,
                    )
                    self._quote_cache[sym] = (now, tick)
                    return tick
            except Exception as e:
                logger.warning(f"Finnhub quote parse error for {sym}: {e}. Using fallback.")

        return await super().get_quotes(sym)

    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]:
        """Fetches historical candlestick bars from Finnhub /stock/candle with 60s TTL cache."""
        sym = symbol.upper()
        cache_key = f"{sym}_{timeframe}_{limit}"
        now = time.monotonic()

        if cache_key in self._ohlcv_cache:
            ts, cached_candles = self._ohlcv_cache[cache_key]
            if now - ts < 60.0:
                return cached_candles

        if not self._has_valid_credentials():
            return await super().get_ohlcv(sym, timeframe, limit)

        to_dt = int(datetime.utcnow().timestamp())
        resolution = "D" if timeframe == "1d" else ("60" if timeframe == "1h" else "D")
        from_dt = int((datetime.utcnow() - timedelta(days=limit * 2)).timestamp())

        res = await self._get(
            "/stock/candle",
            params={
                "symbol": sym,
                "resolution": resolution,
                "from": from_dt,
                "to": to_dt,
            },
        )
        if res and res.status_code == 200:
            try:
                data = res.json()
                if data.get("s") == "ok" and data.get("c"):
                    closes = data.get("c", [])
                    highs = data.get("h", [])
                    lows = data.get("l", [])
                    opens = data.get("o", [])
                    timestamps = data.get("t", [])
                    volumes = data.get("v", [])

                    candles = []
                    n = len(closes)
                    for i in range(max(0, n - limit), n):
                        dt = datetime.utcfromtimestamp(timestamps[i]) if i < len(timestamps) else datetime.utcnow()
                        c = float(closes[i])
                        h = float(highs[i]) if i < len(highs) else c
                        l = float(lows[i]) if i < len(lows) else c
                        o = float(opens[i]) if i < len(opens) else c
                        v = float(volumes[i]) if i < len(volumes) else 1000.0
                        vwap = round((h + l + c) / 3.0, 2)

                        candles.append(
                            Candle(
                                symbol=sym,
                                timestamp=dt,
                                open=o,
                                high=h,
                                low=l,
                                close=c,
                                volume=v,
                                vwap=vwap,
                                trades_count=1000,
                            )
                        )
                    if candles:
                        self._ohlcv_cache[cache_key] = (now, candles)
                        return candles
            except Exception as e:
                logger.warning(f"Finnhub OHLCV parse error for {sym}: {e}. Using fallback.")

        return await super().get_ohlcv(sym, timeframe, limit)

    async def get_fundamental_metrics(self, symbol: str) -> Dict[str, float]:
        """
        Fetches genuine corporate financial statements and valuation ratios
        from Finnhub /stock/metric?metric=all endpoint with 1-hour TTL cache.
        """
        sym = symbol.upper()
        now = time.monotonic()
        ttl = getattr(settings, "FINNHUB_FUNDAMENTALS_CACHE_TTL", 3600)

        # Check in-memory cache
        if sym in self._fundamentals_cache:
            ts, cached_metrics = self._fundamentals_cache[sym]
            if now - ts < ttl:
                return cached_metrics

        if not self._has_valid_credentials():
            return {}

        res = await self._get("/stock/metric", params={"symbol": sym, "metric": "all"})
        if res and res.status_code == 200:
            try:
                m = res.json().get("metric", {})
                metrics: Dict[str, float] = {}

                # Valuation & Earnings Multiples
                pe = m.get("peNormalizedAnnual") or m.get("peTTM") or m.get("peBasicExclExtraTTM")
                if pe is not None and pe > 0:
                    metrics["pe_ratio"] = round(float(pe), 2)

                # Return on Equity (ROE)
                roe = m.get("roeTTM") or m.get("roeRfy")
                if roe is not None:
                    # Finnhub returns ROE in percentage (e.g. 28.5 -> 0.285)
                    metrics["roe"] = round(float(roe) / 100.0 if float(roe) > 1.0 else float(roe), 4)

                # Debt to Equity
                de = m.get("totalDebt/totalEquityQuarterly") or m.get("totalDebt/totalEquityAnnual")
                if de is not None and de > 0:
                    metrics["debt_to_equity"] = round(float(de) / 100.0 if float(de) > 5.0 else float(de), 2)

                # Free Cash Flow Yield
                fcf = m.get("freeCashFlowYieldTTM") or m.get("fcfMarginTTM")
                if fcf is not None:
                    metrics["fcf_yield"] = round(float(fcf) / 100.0 if float(fcf) > 1.0 else float(fcf), 4)

                # Price to Book
                pb = m.get("pbAnnual") or m.get("pbQuarterly")
                if pb is not None and pb > 0:
                    metrics["pb_ratio"] = round(float(pb), 2)

                # Beta
                beta = m.get("beta")
                if beta is not None:
                    metrics["beta"] = round(float(beta), 2)

                self._fundamentals_cache[sym] = (now, metrics)
                return metrics
            except Exception as e:
                logger.warning(f"Finnhub fundamental metrics parse error for {sym}: {e}")

        return {}

    async def get_company_news(self, symbol: str, limit: int = 10) -> List[str]:
        """
        Fetches live textual company news articles from Finnhub /company-news with 15-min TTL cache.
        """
        sym = symbol.upper()
        now = time.monotonic()
        ttl = getattr(settings, "FINNHUB_NEWS_CACHE_TTL", 900)

        if sym in self._news_cache:
            ts, cached_news = self._news_cache[sym]
            if now - ts < ttl:
                return cached_news[:limit]

        if not self._has_valid_credentials():
            return []

        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        start_str = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

        res = await self._get(
            "/company-news",
            params={
                "symbol": sym,
                "from": start_str,
                "to": today_str,
            },
        )
        if res and res.status_code == 200:
            try:
                articles = res.json()
                headlines = []
                for art in articles[:limit]:
                    hl = art.get("headline", "").strip()
                    if hl and hl not in headlines:
                        headlines.append(hl)
                self._news_cache[sym] = (now, headlines)
                return headlines
            except Exception as e:
                logger.warning(f"Finnhub company news parse error for {sym}: {e}")

        return []

    async def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches NLP news sentiment scores from Finnhub /news-sentiment with 15-min TTL cache.
        """
        sym = symbol.upper()
        now = time.monotonic()
        ttl = getattr(settings, "FINNHUB_NEWS_CACHE_TTL", 900)

        if sym in self._sentiment_cache:
            ts, cached_sent = self._sentiment_cache[sym]
            if now - ts < ttl:
                return cached_sent

        if not self._has_valid_credentials():
            return {}

        res = await self._get("/news-sentiment", params={"symbol": sym})
        if res and res.status_code == 200:
            try:
                data = res.json()
                sent = data.get("sentiment", {})
                bull_pct = float(sent.get("bullishPercent", 0.5))
                bear_pct = float(sent.get("bearishPercent", 0.5))
                score = round(bull_pct - bear_pct, 2)
                sentiment_dict = {
                    "sentiment_score": score,
                    "bullish_percentage": bull_pct,
                    "bearish_percentage": bear_pct,
                    "company_news_score": float(data.get("companyNewsScore", 0.5)),
                }
                self._sentiment_cache[sym] = (now, sentiment_dict)
                return sentiment_dict
            except Exception as e:
                logger.warning(f"Finnhub news sentiment parse error for {sym}: {e}")

        return {}


finnhub_data_provider = FinnhubMarketDataProvider()
