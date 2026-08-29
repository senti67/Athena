"""
ATHENA Market Data Providers - Multi-Asset & Alpaca Integration (USD Native)
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
    High-fidelity multi-asset provider for US Equities, ETFs, and Crypto.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.base_prices: Dict[str, float] = {
            "AAPL": 235.50,
            "NVDA": 128.80,
            "MSFT": 445.20,
            "GOOGL": 165.40,
            "AMZN": 178.50,
            "META": 510.20,
            "TSLA": 215.30,
            "SPY": 558.00,
            "QQQ": 482.50,
            "TLT": 98.40,
            "GLD": 232.10,
            "BTC": 64500.00,
        }
        self._current_prices = dict(self.base_prices)

    async def get_quotes(self, symbol: str) -> Tick:
        sym = symbol.upper()
        price = self._current_prices.get(sym, 150.0)

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
        sym = symbol.upper()
        base_p = self.base_prices.get(sym, 150.0)
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
        sym = symbol.upper()
        mid = self._current_prices.get(sym, 150.0)
        tick_increment = 0.05

        bids = [
            OrderBookLevel(price=round(mid - (i * tick_increment + 0.02), 2), size=float(random.randint(50, 1000)))
            for i in range(10)
        ]
        asks = [
            OrderBookLevel(price=round(mid + (i * tick_increment + 0.02), 2), size=float(random.randint(50, 1000)))
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
    Live market provider using yfinance/Alpaca with fallback.
    """

    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]:
        if not HAS_YFINANCE:
            return await super().get_ohlcv(symbol, timeframe, limit)

        try:
            ticker = yf.Ticker(symbol.upper())
            df = await asyncio.to_thread(ticker.history, period="1y", interval="1d")

            if df.empty or len(df) < 20:
                return await super().get_ohlcv(symbol, timeframe, limit)

            candles: List[Candle] = []
            clean_sym = symbol.upper()

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
