"""
ATHENA Market Data Providers - Real-Time Indian NSE / Global Data Feeds (INR)
"""

import asyncio
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Protocol
from packages.schemas.market import AssetInfo, Candle, OrderBookLevel, OrderBookSnapshot, Tick

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


class MarketDataProvider(Protocol):
    """Abstract protocol for all market data ingestion adapters."""

    async def get_quotes(self, symbol: str) -> Tick: ...
    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]: ...
    async def get_order_book(self, symbol: str) -> OrderBookSnapshot: ...


class MockMarketDataProvider:
    """
    High-fidelity Indian Markets (NSE / BSE in INR) & Global multi-asset provider.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.base_prices: Dict[str, float] = {
            "RELIANCE": 2980.50,
            "TCS": 4180.20,
            "HDFCBANK": 1645.00,
            "INFY": 1840.10,
            "ICICIBANK": 1215.30,
            "TATAMOTORS": 985.40,
            "ITC": 495.20,
            "SBIN": 815.50,
            "BHARTIARTL": 1560.00,
            "LT": 3620.00,
            "NIFTY50": 24850.00,
            "BANKNIFTY": 51200.00,
            # Global / Cross-asset benchmarks
            "AAPL": 19600.00,   # INR converted (~$235)
            "NVDA": 10700.00,   # INR converted (~$128)
            "MSFT": 37100.00,   # INR converted (~$445)
            "SPY": 46500.00,
            "GLD": 19500.00,
            "BTC": 5400000.00,  # ~₹54 Lakhs
        }
        self._current_prices = dict(self.base_prices)

    async def get_quotes(self, symbol: str) -> Tick:
        sym = symbol.upper().replace(".NS", "").replace("^", "")
        price = self._current_prices.get(sym, 1000.0)

        # Dynamic drift
        drift = random.gauss(0.0001, 0.002)
        price = round(price * (1.0 + drift), 2)
        self._current_prices[sym] = price

        spread = round(price * 0.0003, 2)
        bid = round(price - spread / 2.0, 2)
        ask = round(price + spread / 2.0, 2)

        return Tick(
            symbol=sym,
            timestamp=datetime.utcnow(),
            price=price,
            size=float(random.randint(10, 500)),
            bid=bid,
            ask=ask,
            bid_size=float(random.randint(100, 2000)),
            ask_size=float(random.randint(100, 2000)),
        )

    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]:
        sym = symbol.upper().replace(".NS", "").replace("^", "")
        base_p = self.base_prices.get(sym, 1000.0)
        candles: List[Candle] = []
        current_p = base_p * 0.88

        now = datetime.utcnow()
        for i in range(limit):
            dt = now - timedelta(days=(limit - i))
            drift = 0.0007 + random.gauss(0.0, 0.014)
            open_p = current_p
            close_p = round(open_p * (1.0 + drift), 2)
            high_p = round(max(open_p, close_p) * (1.0 + abs(random.gauss(0.0, 0.006))), 2)
            low_p = round(min(open_p, close_p) * (1.0 - abs(random.gauss(0.0, 0.006))), 2)
            volume = float(random.randint(500000, 10000000))
            vwap = round((high_p + low_p + close_p) / 3.0, 2)

            candles.append(
                Candle(
                    symbol=sym,
                    timestamp=dt,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=volume,
                    vwap=vwap,
                    trades_count=random.randint(5000, 50000),
                )
            )
            current_p = close_p

        self._current_prices[sym] = current_p
        return candles

    async def get_order_book(self, symbol: str) -> OrderBookSnapshot:
        sym = symbol.upper().replace(".NS", "").replace("^", "")
        mid = self._current_prices.get(sym, 1000.0)
        tick_increment = 0.50 if mid > 1000 else 0.05

        bids = [
            OrderBookLevel(price=round(mid - (i * tick_increment + 0.10), 2), size=float(random.randint(50, 1000)))
            for i in range(10)
        ]
        asks = [
            OrderBookLevel(price=round(mid + (i * tick_increment + 0.10), 2), size=float(random.randint(50, 1000)))
            for i in range(10)
        ]
        bid_vol = sum(b.size for b in bids)
        ask_vol = sum(a.size for a in asks)
        imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol) if (bid_vol + ask_vol) > 0 else 0.0

        return OrderBookSnapshot(
            symbol=sym,
            timestamp=datetime.utcnow(),
            bids=bids,
            asks=asks,
            spread=round(asks[0].price - bids[0].price, 2),
            mid_price=round(mid, 2),
            imbalance=round(imbalance, 4),
        )


class RealMarketDataProvider(MockMarketDataProvider):
    """
    Live market provider using yfinance for Indian NSE equities and global tickers,
    with seamless fallback to simulated real-price models.
    """

    def _get_ticker_symbol(self, symbol: str) -> str:
        sym = symbol.upper().strip()
        if sym in ("NIFTY50", "NIFTY", "^NSEI"):
            return "^NSEI"
        if sym in ("BANKNIFTY", "^NSEBANK"):
            return "^NSEBANK"
        if not sym.endswith(".NS") and not sym.startswith("^") and sym not in ("AAPL", "NVDA", "MSFT", "SPY", "QQQ", "BTC"):
            return f"{sym}.NS"
        return sym

    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]:
        if not HAS_YFINANCE:
            return await super().get_ohlcv(symbol, timeframe, limit)

        ticker_sym = self._get_ticker_symbol(symbol)
        try:
            # Run yfinance in thread pool to avoid blocking async event loop
            ticker = yf.Ticker(ticker_sym)
            df = await asyncio.to_thread(ticker.history, period="1y", interval="1d")

            if df.empty or len(df) < 20:
                return await super().get_ohlcv(symbol, timeframe, limit)

            candles: List[Candle] = []
            clean_sym = symbol.upper().replace(".NS", "").replace("^", "")

            for idx, row in df.tail(limit).iterrows():
                dt = idx.to_pydatetime().replace(tzinfo=None)
                op = round(float(row["Open"]), 2)
                hi = round(float(row["High"]), 2)
                lo = round(float(row["Low"]), 2)
                cl = round(float(row["Close"]), 2)
                vol = float(row.get("Volume", 100000))
                vw = round((hi + lo + cl) / 3.0, 2)

                candles.append(
                    Candle(
                        symbol=clean_sym,
                        timestamp=dt,
                        open=op,
                        high=hi,
                        low=lo,
                        close=cl,
                        volume=vol,
                        vwap=vw,
                    )
                )

            if candles:
                self._current_prices[clean_sym] = candles[-1].close
                return candles

        except Exception:
            pass

        return await super().get_ohlcv(symbol, timeframe, limit)


class HistoricalSeedDataProvider(RealMarketDataProvider):
    """Provider specifically configured for backtesting and historical seeding."""
    pass
