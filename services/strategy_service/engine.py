"""
ATHENA Quantitative Strategy Engine
Coordinates the 6 active production quantitative strategies, applies dynamic Market Regime
suitability weighting, and selects qualified candidate setups based on expected edge.
"""

from typing import Dict, List, Optional, Tuple
from packages.common.config import settings
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentContext
from packages.schemas.strategy import StrategyOutput, StrategySignal, StrategyType
from .base import BaseStrategy
from .strategies import (
    BreakoutStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    PullbackStrategy,
    TrendFollowingStrategy,
    VolatilitySwingStrategy,
)

logger = get_logger("athena.strategy_engine")


class StrategyEngine:
    """
    Evaluates the 6 active quantitative strategies against real market features,
    applies regime suitability weighting, and outputs qualified trade setups.
    """

    def __init__(self):
        self.active_strategies: Dict[StrategyType, BaseStrategy] = {
            StrategyType.TREND_FOLLOWING: TrendFollowingStrategy(),
            StrategyType.MOMENTUM: MomentumStrategy(),
            StrategyType.MEAN_REVERSION: MeanReversionStrategy(),
            StrategyType.BREAKOUT: BreakoutStrategy(),
            StrategyType.PULLBACK: PullbackStrategy(),
            StrategyType.VOLATILITY_SWING: VolatilitySwingStrategy(),
        }

    def evaluate_strategies(
        self, context: AgentContext
    ) -> Tuple[Optional[StrategyOutput], Dict[str, StrategyOutput]]:
        """
        Executes active strategies and applies regime suitability weights.
        
        Returns:
            Tuple of (best_qualified_setup, all_strategy_outputs)
        """
        results: Dict[str, StrategyOutput] = {}
        qualified_setups: List[StrategyOutput] = []

        suitability_weights = {}
        if context.regime_state and context.regime_state.strategy_suitability_weights:
            suitability_weights = context.regime_state.strategy_suitability_weights

        min_conf = getattr(settings, "ATHENA_MIN_SIGNAL_SCORE", getattr(settings, "MIN_STRATEGY_CONFIDENCE", 0.60))
        min_rr = getattr(settings, "ATHENA_MIN_RISK_REWARD", getattr(settings, "MIN_RISK_REWARD_RATIO", 1.8))
        min_edge = getattr(settings, "ATHENA_MIN_EXPECTED_EDGE", 0.012)

        for st_type, strategy in self.active_strategies.items():
            try:
                out = strategy.generate_signal(context)

                # Apply regime suitability weight scaling
                weight = suitability_weights.get(st_type.value, 1.0)
                if weight != 1.0 and out.confidence > 0:
                    scaled_conf = min(1.0, max(0.0, out.confidence * weight))
                    out.confidence = round(scaled_conf, 2)
                    out.regime_compatibility = round(weight, 2)
                    out.rationale += f" [Regime suitability weight: {weight:.2f}x]"

                results[st_type.value] = out

                # Check qualification threshold
                if (
                    out.signal == StrategySignal.BUY
                    and out.confidence >= min_conf
                    and out.risk_reward >= min_rr
                    and out.expected_edge >= min_edge
                ):
                    qualified_setups.append(out)

            except Exception as e:
                logger.error(f"Strategy {st_type.value} error on {context.symbol}: {str(e)}", exc_info=True)

        # Select highest quality candidate setup (sorted by expected edge, confidence, and R:R)
        best_setup: Optional[StrategyOutput] = None
        if qualified_setups:
            qualified_setups.sort(key=lambda s: (s.expected_edge, s.confidence, s.risk_reward), reverse=True)
            best_setup = qualified_setups[0]

        return best_setup, results


strategy_engine = StrategyEngine()
