"""
ATHENA Finnhub Market Data & Financial Intelligence Provider
Integrates with Finnhub REST API (https://finnhub.io/api/v1) for real-time US quotes,
historical candlestick bars, fundamental metrics, and institutional news sentiment.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
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
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__()
        self.api_key = api_key or settings.FINNHUB_API_KEY or ""
        self.base_url = (base_url or settings.FINNHUB_BASE_URL or "https://finnhub.io/api/v1").rstrip("/")
        self.headers = {
            "X-Finnhub-Token": self.api_key,
            "Content-Type": "application/json",
        }

    def _has_valid_credentials(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5 and not self.api_key.startswith("MOCK"))

    async def get_quotes(self, symbol: str) -> Tick:
        """Fetches real-time price quote from Finnhub /quote endpoint."""
        sym = symbol.upper()
        if not self._has_valid_credentials():
            return await super().get_quotes(sym)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": sym, "token": self.api_key},
                )
                if res.status_code == 200:
                    data = res.json()
                    c = float(data.get("c", 0.0))  # Current price
                    if c > 0:
                        h = float(data.get("h", c))
                        l = float(data.get("l", c))
                        o = float(data.get("o", c))
                        spread = round(c * 0.0003, 2)
                        return Tick(
                            symbol=sym,
                            timestamp=datetime.utcnow(),
                            price=c,
                            size=100.0,
                            bid=round(c - spread / 2.0, 2),
                            ask=round(c + spread / 2.0, 2),
                            bid_size=100.0,
                            ask_size=100.0,
                        )
            except Exception as e:
                logger.warning(f"Finnhub quote fetch error for {sym}: {e}. Using fallback.")

        return await super().get_quotes(sym)

    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]:
        """Fetches historical candlestick bars from Finnhub /stock/candle endpoint."""
        sym = symbol.upper()
        if not self._has_valid_credentials():
            return await super().get_ohlcv(sym, timeframe, limit)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                to_dt = int(datetime.utcnow().timestamp())
                # Timeframe mapping
                resolution = "D" if timeframe == "1d" else ("60" if timeframe == "1h" else "D")
                from_dt = int((datetime.utcnow() - timedelta(days=limit * 2)).timestamp())

                res = await client.get(
                    f"{self.base_url}/stock/candle",
                    params={
                        "symbol": sym,
                        "resolution": resolution,
                        "from": from_dt,
                        "to": to_dt,
                        "token": self.api_key,
                    },
                )
                if res.status_code == 200:
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
                            return candles
            except Exception as e:
                logger.warning(f"Finnhub OHLCV fetch error for {sym}: {e}. Using fallback.")

        return await super().get_ohlcv(sym, timeframe, limit)

    async def get_fundamental_metrics(self, symbol: str) -> Dict[str, float]:
        """
        Fetches genuine corporate financial statements and valuation ratios
        from Finnhub /stock/metric?metric=all endpoint.
        """
        sym = symbol.upper()
        if not self._has_valid_credentials():
            return {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(
                    f"{self.base_url}/stock/metric",
                    params={"symbol": sym, "metric": "all", "token": self.api_key},
                )
                if res.status_code == 200:
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

                    return metrics
            except Exception as e:
                logger.warning(f"Finnhub fundamental metrics fetch error for {sym}: {e}")

        return {}

    async def get_company_news(self, symbol: str, limit: int = 10) -> List[str]:
        """
        Fetches live textual company news articles from Finnhub /company-news endpoint.
        """
        sym = symbol.upper()
        if not self._has_valid_credentials():
            return []

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                today_str = datetime.utcnow().strftime("%Y-%m-%d")
                start_str = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
                res = await client.get(
                    f"{self.base_url}/company-news",
                    params={
                        "symbol": sym,
                        "from": start_str,
                        "to": today_str,
                        "token": self.api_key,
                    },
                )
                if res.status_code == 200:
                    articles = res.json()
                    headlines = []
                    for art in articles[:limit]:
                        hl = art.get("headline", "").strip()
                        if hl and hl not in headlines:
                            headlines.append(hl)
                    return headlines
            except Exception as e:
                logger.warning(f"Finnhub company news fetch error for {sym}: {e}")

        return []

    async def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches NLP news sentiment scores from Finnhub /news-sentiment endpoint.
        """
        sym = symbol.upper()
        if not self._has_valid_credentials():
            return {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(
                    f"{self.base_url}/news-sentiment",
                    params={"symbol": sym, "token": self.api_key},
                )
                if res.status_code == 200:
                    data = res.json()
                    sent = data.get("sentiment", {})
                    bull_pct = float(sent.get("bullishPercent", 0.5))
                    bear_pct = float(sent.get("bearishPercent", 0.5))
                    score = round(bull_pct - bear_pct, 2)
                    return {
                        "sentiment_score": score,
                        "bullish_percentage": bull_pct,
                        "bearish_percentage": bear_pct,
                        "company_news_score": float(data.get("companyNewsScore", 0.5)),
                    }
            except Exception as e:
                logger.warning(f"Finnhub news sentiment fetch error for {sym}: {e}")

        return {}


finnhub_data_provider = FinnhubMarketDataProvider()
