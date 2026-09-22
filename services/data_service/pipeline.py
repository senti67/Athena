"""
ATHENA Ingestion & Data Quality Pipeline
Orchestrates raw market data fetching, DQA scoring, fundamental feeds, and news streams.
"""

from typing import Any, Dict, List, Optional
from packages.common.config import settings
from packages.common.exceptions import DataQualityException
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.events import Event, EventType
from packages.schemas.market import Candle, DataQualityReport, OrderBookSnapshot, Tick
from .providers import MarketDataProvider, MockMarketDataProvider
from .alpaca_provider import AlpacaMarketDataProvider
from .finnhub_provider import FinnhubMarketDataProvider, finnhub_data_provider
from .quality import DataQualityAgent

logger = get_logger("athena.data_pipeline")


def _get_default_provider() -> MarketDataProvider:
    provider_type = getattr(settings, "MARKET_DATA_PROVIDER", "alpaca").lower()
    has_finnhub = bool(settings.FINNHUB_API_KEY and len(settings.FINNHUB_API_KEY) > 5)
    has_alpaca = bool(settings.ALPACA_API_KEY and not settings.ALPACA_API_KEY.startswith("PK_MOCK"))

    if provider_type == "finnhub" and has_finnhub:
        return FinnhubMarketDataProvider()
    elif (provider_type in ["alpaca", "paper", "live"]) and has_alpaca:
        return AlpacaMarketDataProvider()
    elif has_finnhub:
        return FinnhubMarketDataProvider()
    elif has_alpaca:
        return AlpacaMarketDataProvider()
    return MockMarketDataProvider()


class DataPipeline:
    """End-to-end data ingestion, validation, and normalization pipeline."""

    def __init__(self, provider: Optional[MarketDataProvider] = None):
        self.provider = provider or _get_default_provider()
        self.finnhub = finnhub_data_provider
        self.quality_agent = DataQualityAgent()
        self._candle_cache: Dict[str, List[Candle]] = {}

    async def ingest_candles(
        self, symbol: str, timeframe: str = "1d", limit: int = 200
    ) -> List[Candle]:
        """Fetches, validates with DataQualityAgent, and caches historical candles."""
        candles = await self.provider.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
        report: DataQualityReport = self.quality_agent.evaluate_candles(symbol, candles)

        if not report.is_valid:
            error_msg = f"Data quality validation failed for {symbol}: score={report.data_quality_score}, reasons={report.rejection_reasons}"
            logger.error(error_msg)
            await event_bus.publish(
                Event(
                    event_type=EventType.DATA_QUALITY_FAILED,
                    payload={"symbol": symbol, "score": report.data_quality_score, "reasons": report.rejection_reasons},
                )
            )
            raise DataQualityException(error_msg, details=report.model_dump())

        self._candle_cache[symbol] = candles

        await event_bus.publish(
            Event(
                event_type=EventType.MARKET_DATA_RECEIVED,
                payload={"symbol": symbol, "bars_count": len(candles), "latest_close": candles[-1].close},
            )
        )
        return candles

    async def get_cached_candles(self, symbol: str) -> List[Candle]:
        if symbol not in self._candle_cache:
            return await self.ingest_candles(symbol)
        return self._candle_cache[symbol]

    async def get_realtime_quote(self, symbol: str) -> Tick:
        tick = await self.provider.get_quotes(symbol)
        valid, score, reasons = self.quality_agent.evaluate_tick(tick)
        if not valid:
            logger.warning(f"Invalid tick for {symbol}: {reasons}")
        return tick

    async def get_order_book(self, symbol: str) -> OrderBookSnapshot:
        return await self.provider.get_order_book(symbol)

    async def get_fundamental_metrics(self, symbol: str) -> Dict[str, float]:
        """Fetches live corporate financial statement metrics from Finnhub if available."""
        if hasattr(self.provider, "get_fundamental_metrics"):
            metrics = await self.provider.get_fundamental_metrics(symbol)
            if metrics:
                return metrics
        return await self.finnhub.get_fundamental_metrics(symbol)

    async def get_company_news(self, symbol: str, limit: int = 10) -> List[str]:
        """Fetches live textual news headlines from Finnhub if available."""
        if hasattr(self.provider, "get_company_news"):
            news = await self.provider.get_company_news(symbol, limit=limit)
            if news:
                return news
        return await self.finnhub.get_company_news(symbol, limit=limit)

    async def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Fetches quantitative NLP news sentiment scores from Finnhub if available."""
        if hasattr(self.provider, "get_news_sentiment"):
            sent = await self.provider.get_news_sentiment(symbol)
            if sent:
                return sent
        return await self.finnhub.get_news_sentiment(symbol)


data_pipeline = DataPipeline()
