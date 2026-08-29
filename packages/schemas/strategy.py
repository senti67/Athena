"""
ATHENA Quantitative Strategy Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StrategyType(str, Enum):
    TREND_FOLLOWING = "trend_following"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    SWING = "swing"
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    PAIRS = "pairs"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    SECTOR_ROTATION = "sector_rotation"
    VALUE = "value"
    GROWTH = "growth"
    EVENT_DRIVEN = "event_driven"
    NEWS = "news"
    VOLATILITY = "volatility"
    MACHINE_LEARNING = "machine_learning"
    REINFORCEMENT_LEARNING = "reinforcement_learning"


class StrategySignal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class StrategyOutput(BaseModel):
    strategy: StrategyType
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signal: StrategySignal
    confidence: float = Field(ge=0.0, le=1.0)
    expected_return: float = Field(default=0.0)
    expected_drawdown: float = Field(default=0.0)
    holding_period: str = "5D"
    stop_loss_pct: float = 0.03
    take_profit_pct: float = 0.06
    indicators_used: Dict[str, float] = Field(default_factory=dict)
    rationale: str = ""
    historical_sharpe: float = 1.2
    win_rate: float = 0.55
