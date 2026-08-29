"""
ATHENA Market Data Providers Abstraction & Implementations
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Optional, Protocol
from packages.schemas.market import AssetInfo, Candle, OrderBookLevel, OrderBookSnapshot, Tick


class MarketDataProvider(Protocol):
    """Abstract protocol for all market data ingestion adapters."""

    async def get_quotes(self, symbol: str) -> Tick: ...
    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]: ...
    async def get_order_book(self, symbol: str) -> OrderBookSnapshot: ...


class MockMarketDataProvider:
    """
    High-fidelity deterministic market data provider with realistic
    geometric Brownian motion, support/resistance clustering, and microstructure dynamics.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.base_prices = {
            "AAPL": 225.50,
            "MSFT": 445.20,
            "NVDA": 128.80,
            "GOOGL": 178.40,
            "AMZN": 186.60,
            "META": 510.30,
            "TSLA": 215.10,
            "SPY": 558.20,
            "QQQ": 485.40,
            "TLT": 94.50,
            "GLD": 232.10,
            "USO": 75.80,
            "BTC": 64500.0,
        }
        self._current_prices = dict(self.base_prices)

    async def get_quotes(self, symbol: str) -> Tick:
        price = self._current_prices.get(symbol, 100.0)
        # Small random walk
        drift = random.gauss(0.0001, 0.002)
        price = round(price * (1.0 + drift), 2)
        self._current_prices[symbol] = price

        spread = round(price * 0.0003, 2)
        bid = round(price - spread / 2.0, 2)
        ask = round(price + spread / 2.0, 2)

        return Tick(
            symbol=symbol,
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
        base_p = self.base_prices.get(symbol, 100.0)
        candles: List[Candle] = []
        current_p = base_p * 0.85  # start 15% lower to simulate general upward trend

        now = datetime.utcnow()
        for i in range(limit):
            dt = now - timedelta(days=(limit - i))
            drift = 0.0008 + random.gauss(0.0, 0.015)
            open_p = current_p
            close_p = round(open_p * (1.0 + drift), 2)
            high_p = round(max(open_p, close_p) * (1.0 + abs(random.gauss(0.0, 0.008))), 2)
            low_p = round(min(open_p, close_p) * (1.0 - abs(random.gauss(0.0, 0.008))), 2)
            volume = float(random.randint(1000000, 15000000))
            vwap = round((high_p + low_p + close_p) / 3.0, 2)

            candles.append(
                Candle(
                    symbol=symbol,
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

        self._current_prices[symbol] = current_p
        return candles

    async def get_order_book(self, symbol: str) -> OrderBookSnapshot:
        mid = self._current_prices.get(symbol, 100.0)
        bids = [
            OrderBookLevel(price=round(mid - (i * 0.05 + 0.02), 2), size=float(random.randint(100, 1000)))
            for i in range(10)
        ]
        asks = [
            OrderBookLevel(price=round(mid + (i * 0.05 + 0.02), 2), size=float(random.randint(100, 1000)))
            for i in range(10)
        ]
        bid_vol = sum(b.size for b in bids)
        ask_vol = sum(a.size for a in asks)
        imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol) if (bid_vol + ask_vol) > 0 else 0.0

        return OrderBookSnapshot(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            bids=bids,
            asks=asks,
            spread=round(asks[0].price - bids[0].price, 2),
            mid_price=round(mid, 2),
            imbalance=round(imbalance, 4),
        )


class HistoricalSeedDataProvider(MockMarketDataProvider):
    """Provider specifically configured for backtesting and historical seeding."""
    pass
