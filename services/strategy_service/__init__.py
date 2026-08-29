"""Athena Strategy Service Package"""

from .base import BaseStrategy
from .registry import StrategyRegistry, strategy_registry
from .strategies import (
    TrendFollowingStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    SwingTradingStrategy,
    BreakoutStrategy,
    PullbackStrategy,
    PairsTradingStrategy,
    StatisticalArbitrageStrategy,
    SectorRotationStrategy,
    ValueInvestingStrategy,
    GrowthInvestingStrategy,
    EventDrivenStrategy,
    NewsTradingStrategy,
    VolatilityTradingStrategy,
    MachineLearningStrategy,
    ReinforcementLearningStrategy,
)

__all__ = [
    "BaseStrategy",
    "StrategyRegistry",
    "strategy_registry",
    "TrendFollowingStrategy",
    "MomentumStrategy",
    "MeanReversionStrategy",
    "SwingTradingStrategy",
    "BreakoutStrategy",
    "PullbackStrategy",
    "PairsTradingStrategy",
    "StatisticalArbitrageStrategy",
    "SectorRotationStrategy",
    "ValueInvestingStrategy",
    "GrowthInvestingStrategy",
    "EventDrivenStrategy",
    "NewsTradingStrategy",
    "VolatilityTradingStrategy",
    "MachineLearningStrategy",
    "ReinforcementLearningStrategy",
]
