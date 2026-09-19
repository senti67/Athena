"""
ATHENA Disabled & Experimental Strategies
Contains the 11 inactive/experimental strategies marked as non-operational.
These do not generate active production trading signals.
"""

from packages.schemas.agent import AgentContext, ImplementationStatus
from packages.schemas.strategy import StrategyOutput, StrategySignal, StrategyType
from .base import BaseStrategy


class DisabledStrategy(BaseStrategy):
    """Base class for all disabled/experimental strategies."""
    is_active = False

    def generate_signal(self, context: AgentContext) -> StrategyOutput:
        return StrategyOutput(
            strategy=self.name,
            symbol=context.symbol,
            signal=StrategySignal.UNAVAILABLE,
            confidence=0.0,
            risk_reward=0.0,
            holding_period="0D",
            stop_loss_pct=0.0,
            take_profit_pct=0.0,
            indicators_used={},
            evidence=[],
            rationale=f"Strategy {self.name.value} is experimental/disabled in ATHENA V2 production.",
            historical_sharpe=0.0,
            win_rate=0.0,
            implementation_status=ImplementationStatus.PLACEHOLDER,
            is_active=False,
        )


class SwingTradingStrategy(DisabledStrategy):
    name = StrategyType.SWING
    description = "Multi-day support/resistance swing structure (Experimental)"


class PairsTradingStrategy(DisabledStrategy):
    name = StrategyType.PAIRS
    description = "Statistical co-integration pair trading (Experimental)"


class StatisticalArbitrageStrategy(DisabledStrategy):
    name = StrategyType.STATISTICAL_ARBITRAGE
    description = "Cross-sectional mean reversion arbitrage (Experimental)"


class SectorRotationStrategy(DisabledStrategy):
    name = StrategyType.SECTOR_ROTATION
    description = "Sector relative strength momentum (Experimental)"


class ValueInvestingStrategy(DisabledStrategy):
    name = StrategyType.VALUE
    description = "Fundamental valuation deep value (Experimental)"


class GrowthInvestingStrategy(DisabledStrategy):
    name = StrategyType.GROWTH
    description = "Fundamental revenue & earnings growth (Experimental)"


class EventDrivenStrategy(DisabledStrategy):
    name = StrategyType.EVENT_DRIVEN
    description = "Earnings catalyst and corporate action (Experimental)"


class NewsTradingStrategy(DisabledStrategy):
    name = StrategyType.NEWS
    description = "Real-time news spike momentum (Experimental)"


class VolatilityTradingStrategy(DisabledStrategy):
    name = StrategyType.VOLATILITY
    description = "VIX and implied volatility curve arbitrage (Experimental)"


class MachineLearningStrategy(DisabledStrategy):
    name = StrategyType.MACHINE_LEARNING
    description = "Supervised classifier setup (Experimental)"


class ReinforcementLearningStrategy(DisabledStrategy):
    name = StrategyType.REINFORCEMENT_LEARNING
    description = "Q-learning / PPO policy network (Experimental)"
