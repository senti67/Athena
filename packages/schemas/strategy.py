"""
ATHENA V2 Quantitative Strategy Schemas
Defines the 5 Active Production Strategies, Disabled/Experimental types, and structured outputs.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .agent import ImplementationStatus


class StrategyType(str, Enum):
    """Active and Disabled Strategy Registry."""
    # --- 5 ACTIVE PRODUCTION STRATEGIES ---
    TREND_FOLLOWING = "trend_following"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    PULLBACK = "pullback"

    # --- DISABLED / EXPERIMENTAL STRATEGIES ---
    SWING = "swing"
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
    UNAVAILABLE = "UNAVAILABLE"


class StrategyOutput(BaseModel):
    strategy: StrategyType = Field(alias="strategy_name", default=StrategyType.TREND_FOLLOWING)
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signal: StrategySignal = Field(alias="action", default=StrategySignal.HOLD)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_reward: float = Field(default=2.0, ge=0.0)
    holding_period: str = Field(alias="timeframe", default="5D")
    stop_loss_pct: float = 0.025
    take_profit_pct: float = 0.060
    indicators_used: Dict[str, float] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    data_quality: float = Field(default=1.0, ge=0.0, le=1.0)
    rationale: str = ""
    historical_sharpe: float = 1.5
    win_rate: float = 0.58
    implementation_status: ImplementationStatus = ImplementationStatus.IMPLEMENTED
    is_active: bool = True

    class Config:
        populate_by_name = True

    @property
    def action(self) -> StrategySignal:
        return self.signal

    @property
    def strategy_name(self) -> StrategyType:
        return self.strategy

    @property
    def timeframe(self) -> str:
        return self.holding_period
