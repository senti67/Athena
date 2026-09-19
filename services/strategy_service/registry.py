"""
ATHENA Strategy Execution Registry
Coordinates execution of the 5 active quantitative strategies and provides compatibility lookups.
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
    MeanReversionStrategy,
    MomentumStrategy,
    PullbackStrategy,
    TrendFollowingStrategy,
)
from .experimental_strategies import (
    EventDrivenStrategy,
    GrowthInvestingStrategy,
    MachineLearningStrategy,
    NewsTradingStrategy,
    PairsTradingStrategy,
    ReinforcementLearningStrategy,
    SectorRotationStrategy,
    StatisticalArbitrageStrategy,
    SwingTradingStrategy,
    ValueInvestingStrategy,
    VolatilityTradingStrategy,
)

logger = get_logger("athena.strategy_registry")


class StrategyRegistry:
    """Manages active and disabled strategies."""

    def __init__(self):
        # 5 Active production strategies
        self.active_strategies: Dict[StrategyType, BaseStrategy] = {
            StrategyType.TREND_FOLLOWING: TrendFollowingStrategy(),
            StrategyType.MOMENTUM: MomentumStrategy(),
            StrategyType.MEAN_REVERSION: MeanReversionStrategy(),
            StrategyType.BREAKOUT: BreakoutStrategy(),
            StrategyType.PULLBACK: PullbackStrategy(),
        }
        # 11 Inactive / experimental strategies
        self.experimental_strategies: Dict[StrategyType, BaseStrategy] = {
            StrategyType.SWING: SwingTradingStrategy(),
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

        # Unified lookup dictionary
        self.strategies: Dict[StrategyType, BaseStrategy] = {
            **self.active_strategies,
            **self.experimental_strategies,
        }

    def run_all_strategies(self, context: AgentContext, active_only: bool = True) -> Dict[str, StrategyOutput]:
        """Executes strategies and returns a dictionary of signals."""
        target_pool = self.active_strategies if active_only else self.strategies
        results: Dict[str, StrategyOutput] = {}
        for st_type, strategy in target_pool.items():
            try:
                out = strategy.generate_signal(context)
                results[st_type.value] = out
            except Exception as e:
                logger.error(f"Strategy {st_type.value} error: {str(e)}", exc_info=True)

        return results


strategy_registry = StrategyRegistry()
