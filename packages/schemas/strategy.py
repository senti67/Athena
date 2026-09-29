"""
ATHENA Quantitative Strategy Schemas
Defines Active Production Strategies, Disabled/Quarantined Strategies, expected edge metrics, and structured signals.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .agent import FeatureGroup, ImplementationStatus


class StrategyType(str, Enum):
    """Active and Disabled Strategy Registry."""
    # --- 6 ACTIVE PRODUCTION STRATEGIES ---
    TREND_FOLLOWING = "trend_following"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    VOLATILITY_SWING = "volatility_swing"

    # --- DISABLED / EXPERIMENTAL / PLACEHOLDER STRATEGIES ---
    VOLATILITY = "volatility_swing"
    SWING = "swing"
    PAIRS = "pairs"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    SECTOR_ROTATION = "sector_rotation"
    VALUE = "value"
    GROWTH = "growth"
    EVENT_DRIVEN = "event_driven"
    NEWS = "news"
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
    score: float = Field(default=0.0, description="Strategy directional score [-1.0 to 1.0]")
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    expected_edge: float = Field(default=0.0, description="Estimated directional edge (expected return)")
    expected_value: float = Field(default=0.0, description="P(win)*AvgWin - P(loss)*AvgLoss")
    probability_win: float = Field(default=0.50, ge=0.0, le=1.0)
    risk_reward: float = Field(default=2.0, ge=0.0)
    holding_period: str = Field(alias="timeframe", default="5D")
    stop_loss_pct: float = 0.025
    take_profit_pct: float = 0.060
    feature_group: FeatureGroup = Field(default=FeatureGroup.TREND)
    indicators_used: Dict[str, float] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    data_quality: float = Field(default=1.0, ge=0.0, le=1.0)
    regime_compatibility: float = Field(default=1.0, ge=0.0, le=2.0)
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
