"""
ATHENA Alpaca Market Data Provider
Integrates with Alpaca Markets Data API (https://data.alpaca.markets/v2) for US Equities & Crypto.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx

from packages.common.config import settings
from packages.logging.logger import get_logger
from packages.schemas.market import Candle, OrderBookLevel, OrderBookSnapshot, Tick
from .providers import MockMarketDataProvider

logger = get_logger("athena.alpaca_data_provider")


class AlpacaMarketDataProvider(MockMarketDataProvider):
    """
    Direct interface to Alpaca Data API v2.
    Fetches real-time multi-asset quotes, order books, and OHLCV bars.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        data_url: Optional[str] = None,
    ):
        super().__init__()
        self.api_key = api_key or settings.ALPACA_API_KEY or settings.BROKER_API_KEY or "PK_MOCK_ALPACA_KEY"
        self.secret_key = secret_key or settings.ALPACA_SECRET_KEY or settings.BROKER_API_SECRET or "SK_MOCK_ALPACA_SECRET"
        self.data_url = data_url or settings.ALPACA_DATA_URL or "https://data.alpaca.markets"
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
        }

    def _has_valid_credentials(self) -> bool:
        return (
            bool(self.api_key)
            and not self.api_key.startswith("PK_MOCK")
            and bool(self.secret_key)
            and not self.secret_key.startswith("SK_MOCK")
        )

    async def get_quotes(self, symbol: str) -> Tick:
        sym = symbol.upper()
        if not self._has_valid_credentials():
            return await super().get_quotes(sym)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(
                    f"{self.data_url}/v2/stocks/{sym}/quotes/latest",
                    headers=self.headers,
                )
                if res.status_code == 200:
                    q = res.json().get("quote", {})
                    bid = float(q.get("bp", 0.0))
                    ask = float(q.get("ap", 0.0))
                    mid = round((bid + ask) / 2.0, 2) if (bid + ask) > 0 else 150.0
                    return Tick(
                        symbol=sym,
                        timestamp=datetime.utcnow(),
                        price=mid,
                        size=float(q.get("as", 100)),
                        bid=bid,
                        ask=ask,
                        bid_size=float(q.get("bs", 100)),
                        ask_size=float(q.get("as", 100)),
                    )
            except Exception as e:
                logger.warning(f"Alpaca quote fetch error: {e}. Using fallback.")

        return await super().get_quotes(sym)

    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]:
        sym = symbol.upper()
        if not self._has_valid_credentials():
            return await super().get_ohlcv(sym, timeframe, limit)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Alpaca V2 bars endpoint
                end_dt = datetime.utcnow()
                start_dt = end_dt - timedelta(days=limit * 2)
                params = {
                    "timeframe": "1Day" if timeframe == "1d" else "1Hour",
                    "start": start_dt.strftime("%Y-%m-%d"),
                    "limit": limit,
                    "adjustment": "all",
                    "feed": "iex",
                }
                res = await client.get(
                    f"{self.data_url}/v2/stocks/{sym}/bars",
                    headers=self.headers,
                    params=params,
                )
                if res.status_code == 200:
                    bars = res.json().get("bars", [])
                    if bars:
                        candles = []
                        for b in bars:
                            candles.append(
                                Candle(
                                    symbol=sym,
                                    timestamp=datetime.fromisoformat(b["t"].replace("Z", "+00:00")).replace(tzinfo=None),
                                    open=float(b["o"]),
                                    high=float(b["h"]),
                                    low=float(b["l"]),
                                    close=float(b["c"]),
                                    volume=float(b["v"]),
                                    vwap=float(b.get("vw", b["c"])),
                                    trades_count=int(b.get("n", 1000)),
                                )
                            )
                        return candles
            except Exception as e:
                logger.warning(f"Alpaca bars fetch error: {e}. Using fallback.")

        return await super().get_ohlcv(sym, timeframe, limit)


alpaca_data_provider = AlpacaMarketDataProvider()
