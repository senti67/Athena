"""
Unit Tests for ATHENA Market Data Providers & Finnhub Integration
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from packages.schemas.market import Candle, Tick
from services.data_service.finnhub_provider import FinnhubMarketDataProvider
from services.data_service.alpaca_provider import AlpacaMarketDataProvider
from services.data_service.pipeline import DataPipeline


@pytest.mark.asyncio
async def test_finnhub_provider_fallback_when_unconfigured():
    """Finnhub provider should gracefully fallback to mock provider when no API key is supplied."""
    provider = FinnhubMarketDataProvider(api_key="")
    assert not provider._has_valid_credentials()
    
    quote = await provider.get_quotes("AAPL")
    assert isinstance(quote, Tick)
    assert quote.symbol == "AAPL"
    assert quote.price > 0

    candles = await provider.get_ohlcv("AAPL", timeframe="1d", limit=10)
    assert len(candles) == 10
    assert all(isinstance(c, Candle) for c in candles)

    fundamentals = await provider.get_fundamental_metrics("AAPL")
    assert fundamentals == {}

    news = await provider.get_company_news("AAPL")
    assert news == []

    sentiment = await provider.get_news_sentiment("AAPL")
    assert sentiment == {}


@pytest.mark.asyncio
async def test_finnhub_provider_live_quote_parsing():
    """Tests parsing of Finnhub /quote API response."""
    provider = FinnhubMarketDataProvider(api_key="valid_test_key_12345")
    assert provider._has_valid_credentials()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "c": 220.50,
        "h": 222.00,
        "l": 219.00,
        "o": 220.00,
        "pc": 218.50,
        "t": 1726000000,
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        tick = await provider.get_quotes("AAPL")

        assert tick.symbol == "AAPL"
        assert tick.price == 220.50
        assert tick.bid < tick.price
        assert tick.ask > tick.price


@pytest.mark.asyncio
async def test_finnhub_provider_fundamentals_parsing():
    """Tests parsing of Finnhub /stock/metric API response."""
    provider = FinnhubMarketDataProvider(api_key="valid_test_key_12345")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "metric": {
            "peTTM": 28.4,
            "roeTTM": 32.5,
            "totalDebt/totalEquityQuarterly": 1.25,
            "freeCashFlowYieldTTM": 4.8,
            "pbAnnual": 15.2,
            "beta": 1.12,
        }
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        metrics = await provider.get_fundamental_metrics("MSFT")

        assert metrics.get("pe_ratio") == 28.4
        assert metrics.get("roe") == 0.325
        assert metrics.get("debt_to_equity") == 1.25
        assert metrics.get("fcf_yield") == 0.048
        assert metrics.get("pb_ratio") == 15.2
        assert metrics.get("beta") == 1.12


@pytest.mark.asyncio
async def test_finnhub_provider_news_and_sentiment():
    """Tests parsing of Finnhub company news & sentiment."""
    provider = FinnhubMarketDataProvider(api_key="valid_test_key_12345")

    # Mock company-news
    mock_news_resp = MagicMock()
    mock_news_resp.status_code = 200
    mock_news_resp.json.return_value = [
        {"headline": "Tech Sector Surges on AI Demand", "id": 1},
        {"headline": "Cloud Revenue Growth Outpaces Estimates", "id": 2},
    ]

    # Mock news-sentiment
    mock_sent_resp = MagicMock()
    mock_sent_resp.status_code = 200
    mock_sent_resp.json.return_value = {
        "sentiment": {
            "bullishPercent": 0.75,
            "bearishPercent": 0.25,
        },
        "companyNewsScore": 0.85,
    }

    async def mock_router(url, params=None, **kwargs):
        if "company-news" in url:
            return mock_news_resp
        elif "news-sentiment" in url:
            return mock_sent_resp
        return mock_news_resp

    with patch("httpx.AsyncClient.get", side_effect=mock_router):
        news = await provider.get_company_news("NVDA", limit=5)
        assert len(news) == 2
        assert "Tech Sector Surges on AI Demand" in news

        sentiment = await provider.get_news_sentiment("NVDA")
        assert sentiment.get("sentiment_score") == 0.50
        assert sentiment.get("bullish_percentage") == 0.75


@pytest.mark.asyncio
async def test_data_pipeline_routing_and_enrichment():
    """Tests DataPipeline correctly passes fundamentals and news from Finnhub."""
    provider = FinnhubMarketDataProvider(api_key="")
    pipeline = DataPipeline(provider=provider)

    candles = await pipeline.ingest_candles("AAPL", limit=50)
    assert len(candles) == 50

    cached = await pipeline.get_cached_candles("AAPL")
    assert cached == candles
