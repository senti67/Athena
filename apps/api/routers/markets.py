"""
ATHENA Market Data & Asset Universe Router
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.market import AssetInfo, Candle, OrderBookSnapshot, Tick
from services.data_service.pipeline import data_pipeline
from services.feature_service.pipeline import feature_pipeline

router = APIRouter(prefix="/markets", tags=["Markets"])

DEFAULT_UNIVERSE = [
    AssetInfo(symbol="AAPL", name="Apple Inc.", asset_class="EQUITY", sector="Technology"),
    AssetInfo(symbol="MSFT", name="Microsoft Corp.", asset_class="EQUITY", sector="Technology"),
    AssetInfo(symbol="NVDA", name="NVIDIA Corp.", asset_class="EQUITY", sector="Semiconductors"),
    AssetInfo(symbol="GOOGL", name="Alphabet Inc.", asset_class="EQUITY", sector="Technology"),
    AssetInfo(symbol="AMZN", name="Amazon.com Inc.", asset_class="EQUITY", sector="Consumer Cyclical"),
    AssetInfo(symbol="META", name="Meta Platforms Inc.", asset_class="EQUITY", sector="Technology"),
    AssetInfo(symbol="TSLA", name="Tesla Inc.", asset_class="EQUITY", sector="Auto/EV"),
    AssetInfo(symbol="SPY", name="SPDR S&P 500 ETF", asset_class="ETF", sector="Index"),
    AssetInfo(symbol="QQQ", name="Invesco QQQ Trust", asset_class="ETF", sector="Index"),
    AssetInfo(symbol="TLT", name="iShares 20+ Year Treasury Bond", asset_class="ETF", sector="Fixed Income"),
    AssetInfo(symbol="GLD", name="SPDR Gold Shares", asset_class="COMMODITY", sector="Precious Metals"),
    AssetInfo(symbol="BTC", name="Bitcoin", asset_class="CRYPTO", sector="Digital Assets"),
]


@router.get("", response_model=List[AssetInfo])
async def get_trading_universe():
    return DEFAULT_UNIVERSE


@router.get("/{symbol}", response_model=Tick)
async def get_market_quote(symbol: str):
    sym = symbol.upper()
    return await data_pipeline.get_realtime_quote(sym)


@router.get("/{symbol}/candles", response_model=List[Candle])
async def get_market_candles(
    symbol: str,
    timeframe: str = "1d",
    limit: int = Query(default=150, ge=10, le=500),
):
    sym = symbol.upper()
    return await data_pipeline.ingest_candles(sym, timeframe=timeframe, limit=limit)


@router.get("/{symbol}/orderbook", response_model=OrderBookSnapshot)
async def get_market_orderbook(symbol: str):
    sym = symbol.upper()
    return await data_pipeline.get_order_book(sym)


@router.get("/{symbol}/features", response_model=FeatureSnapshot)
async def get_market_features(symbol: str):
    sym = symbol.upper()
    candles = await data_pipeline.ingest_candles(sym, limit=150)
    return feature_pipeline.compute_features(sym, candles)
