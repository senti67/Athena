"""
ATHENA Market & Data Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AssetInfo(BaseModel):
    symbol: str
    name: str
    asset_class: str = "EQUITY"  # EQUITY, FX, COMMODITY, CRYPTO
    sector: Optional[str] = "Technology"
    currency: str = "USD"
    tick_size: float = 0.01
    lot_size: int = 1
    is_active: bool = True


class Candle(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    trades_count: Optional[int] = None


class Tick(BaseModel):
    symbol: str
    timestamp: datetime
    price: float
    size: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None


class OrderBookLevel(BaseModel):
    price: float
    size: float


class OrderBookSnapshot(BaseModel):
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel] = Field(default_factory=list)
    asks: List[OrderBookLevel] = Field(default_factory=list)
    spread: float = 0.0
    mid_price: float = 0.0
    imbalance: float = 0.0  # (bid_volume - ask_volume) / (bid_volume + ask_volume)


class DataQualityReport(BaseModel):
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: float = Field(ge=0.0, le=1.0, description="0 to 1 data health metric")
    is_valid: bool = True
    missing_points_pct: float = 0.0
    stale_price_detected: bool = False
    abnormal_spread_detected: bool = False
    impossible_price_detected: bool = False
    timestamp_errors: int = 0
    warnings: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
