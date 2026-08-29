"""
ATHENA Strategy Execution Registry
Coordinates execution of all 16 quantitative trading strategies.
"""

from typing import Dict, List, Optional
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentContext
from packages.schemas.events import Event, EventType
from packages.schemas.strategy import StrategyOutput, StrategySignal, StrategyType
from .base import BaseStrategy
from .strategies import (
    BreakoutStrategy,
    EventDrivenStrategy,
    GrowthInvestingStrategy,
    MachineLearningStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    NewsTradingStrategy,
    PairsTradingStrategy,
    PullbackStrategy,
    ReinforcementLearningStrategy,
    SectorRotationStrategy,
    StatisticalArbitrageStrategy,
    SwingTradingStrategy,
    TrendFollowingStrategy,
    ValueInvestingStrategy,
    VolatilityTradingStrategy,
)

logger = get_logger("athena.strategy_registry")


class StrategyRegistry:
    """Manages the pool of 16 quantitative strategies."""

    def __init__(self):
        self.strategies: Dict[StrategyType, BaseStrategy] = {
            StrategyType.TREND_FOLLOWING: TrendFollowingStrategy(),
            StrategyType.MOMENTUM: MomentumStrategy(),
            StrategyType.MEAN_REVERSION: MeanReversionStrategy(),
            StrategyType.SWING: SwingTradingStrategy(),
            StrategyType.BREAKOUT: BreakoutStrategy(),
            StrategyType.PULLBACK: PullbackStrategy(),
            StrategyType.PAIRS: PairsTradingStrategy(),
            StrategyType.STATISTICAL_ARBITRAGE: StatisticalArbitrageStrategy(),
            StrategyType.SECTOR_ROTATION: SectorRotationStrategy(),
            StrategyType.VALUE: ValueInvestingStrategy(),
            StrategyType.GROWTH: GrowthInvestingStrategy(),
            StrategyType.EVENT_DRIVEN: EventDrivenStrategy(),
            StrategyType.NEWS: NewsTradingStrategy(),
            StrategyType.VOLATILITY: VolatilityTradingStrategy(),
            StrategyType.MACHINE_LEARNING: MachineLearningStrategy(),
            StrategyType.REINFORCEMENT_LEARNING: ReinforcementLearningStrategy(),
        }

    def run_all_strategies(self, context: AgentContext) -> Dict[str, StrategyOutput]:
        """Executes all 16 strategies and returns a dictionary of signals."""
        results: Dict[str, StrategyOutput] = {}
        for st_type, strategy in self.strategies.items():
            try:
                out = strategy.generate_signal(context)
                results[st_type.value] = out
            except Exception as e:
                logger.error(f"Strategy {st_type.value} error: {str(e)}", exc_info=True)

        return results


strategy_registry = StrategyRegistry()
