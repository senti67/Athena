"""
ATHENA Quantitative Market Regime Detection Engine
Classifies market regime into 6 distinct states using measurable technical, volatility, and trend metrics.
Dynamically sets strategy and feature group weights.
"""

from datetime import datetime
from typing import Dict, List, Tuple
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.events import Event, EventType
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.regime import MarketRegimeType, RegimeMetrics, RegimeState

logger = get_logger("athena.regime_detector")


class MarketRegimeDetector:
    """
    Quantitative Multi-Factor Market Regime Classifier.
    Evaluates ADX, EMA structure, EMA slope, realized volatility, and Bollinger Bandwidth.
    """

    def detect_regime(self, snapshot: FeatureSnapshot) -> RegimeState:
        tech = snapshot.technical
        stat = snapshot.statistical
        vol = snapshot.volatility
        cross = snapshot.cross_asset
        price = snapshot.current_price

        # 1. Compute quantitative regime metrics
        adx = tech.adx_14
        atr_pct = (tech.atr_14 / price) if price > 0 else 0.015
        realized_vol = vol.realized_vol_20d
        vol_ratio = vol.vol_regime_ratio
        bb_width = tech.bb_bandwidth
        vol_ratio_volume = tech.volume_ratio

        # EMA Stack Trend Score (-1.0 to +1.0)
        ema_score = 0.0
        if tech.ema_9 > tech.ema_21:
            ema_score += 0.35
        else:
            ema_score -= 0.35

        if tech.ema_21 > tech.ema_50:
            ema_score += 0.35
        else:
            ema_score -= 0.35

        if tech.ema_200 > 0:
            if price > tech.ema_200:
                ema_score += 0.30
            else:
                ema_score -= 0.30
        else:
            if price > tech.ema_50:
                ema_score += 0.30
            else:
                ema_score -= 0.30

        ema_slope_20 = (tech.ema_21 - tech.ema_50) / tech.ema_50 if tech.ema_50 > 0 else 0.0

        # Benchmark trend
        bench_trend = "NEUTRAL"
        if cross.spy_return_1d > 0.005:
            bench_trend = "BULLISH"
        elif cross.spy_return_1d < -0.005:
            bench_trend = "BEARISH"

        regime_metrics = RegimeMetrics(
            adx_14=round(adx, 2),
            atr_pct=round(atr_pct, 4),
            ema_trend_score=round(ema_score, 2),
            ema_slope_20=round(ema_slope_20, 4),
            realized_vol_20d=round(realized_vol, 4),
            vol_ratio=round(vol_ratio, 2),
            bb_bandwidth=round(bb_width, 4),
            volume_ratio=round(vol_ratio_volume, 2),
            benchmark_trend=bench_trend,
        )

        # 2. Rule-based Regime Classification
        # A. High Volatility Extreme
        if realized_vol >= 0.38 or atr_pct >= 0.038 or cross.vix_level >= 28.0 or vol_ratio >= 1.85:
            regime = MarketRegimeType.HIGH_VOLATILITY
            confidence = min(0.95, 0.70 + (realized_vol - 0.35) * 0.8)
            desc = "High Volatility Regime: Elevated price variance and wider dispersion. Risk reduction required."

        # B. Low Volatility Squeeze
        elif realized_vol <= 0.12 and bb_width <= 0.035 and adx < 18.0:
            regime = MarketRegimeType.LOW_VOLATILITY
            confidence = 0.85
            desc = "Low Volatility Squeeze: Range compression with subdued volatility, preparing for potential breakout."

        # C. Trending Bull
        elif ema_score >= 0.60 and (adx >= 20.0 or stat.returns_20d > 0.02) and price > tech.ema_50:
            regime = MarketRegimeType.TRENDING_BULL
            confidence = min(0.92, 0.65 + (ema_score * 0.25))
            desc = "Trending Bull: Sustained upward price structure, moving average alignment, and positive momentum."

        # D. Trending Bear
        elif ema_score <= -0.60 and (adx >= 20.0 or stat.returns_20d < -0.02) and price < tech.ema_50:
            regime = MarketRegimeType.TRENDING_BEAR
            confidence = min(0.90, 0.65 + (abs(ema_score) * 0.25))
            desc = "Trending Bear: Downward trend structure with moving averages in bearish descending alignment."

        # E. Sideways / Range-Bound
        elif adx < 22.0 and abs(ema_score) < 0.50:
            regime = MarketRegimeType.SIDEWAYS
            confidence = 0.80
            desc = "Sideways / Range-Bound: Lack of strong directional trend; oscillating between support and resistance."

        # F. Uncertain
        else:
            regime = MarketRegimeType.UNCERTAIN
            confidence = 0.55
            desc = "Uncertain Market State: Mixed trend signals and conflicting volatility profile. Caution advised."

        # 3. Strategy Suitability and Feature Group Allocations
        rec_strategies, strat_weights, group_weights = self._get_allocations(regime)

        state = RegimeState(
            timestamp=datetime.utcnow(),
            symbol_or_market=snapshot.symbol,
            regime=regime,
            confidence=round(confidence, 2),
            description=desc,
            recommended_strategies=rec_strategies,
            strategy_suitability_weights=strat_weights,
            feature_group_weights=group_weights,
            metrics=regime_metrics,
        )

        return state

    def _get_allocations(
        self, regime: MarketRegimeType
    ) -> Tuple[List[str], Dict[str, float], Dict[str, float]]:
        """Returns (recommended_strategies, strategy_weights, feature_group_weights)."""
        if regime == MarketRegimeType.TRENDING_BULL:
            return (
                ["trend_following", "momentum", "breakout", "pullback"],
                {
                    "trend_following": 1.35,
                    "momentum": 1.30,
                    "breakout": 1.20,
                    "pullback": 1.25,
                    "mean_reversion": 0.50,
                    "volatility_swing": 0.70,
                },
                {
                    "trend": 1.35,
                    "momentum": 1.30,
                    "mean_reversion": 0.50,
                    "volatility": 0.80,
                    "fundamental": 1.00,
                    "sentiment": 1.00,
                    "macro": 1.10,
                },
            )

        elif regime == MarketRegimeType.TRENDING_BEAR:
            return (
                ["mean_reversion", "volatility_swing"],
                {
                    "trend_following": 0.60,
                    "momentum": 0.50,
                    "breakout": 0.45,
                    "pullback": 0.60,
                    "mean_reversion": 1.25,
                    "volatility_swing": 1.35,
                },
                {
                    "trend": 0.60,
                    "momentum": 0.50,
                    "mean_reversion": 1.25,
                    "volatility": 1.30,
                    "fundamental": 1.10,
                    "sentiment": 1.00,
                    "macro": 1.20,
                },
            )

        elif regime == MarketRegimeType.SIDEWAYS:
            return (
                ["mean_reversion", "pullback"],
                {
                    "mean_reversion": 1.40,
                    "pullback": 1.15,
                    "trend_following": 0.55,
                    "momentum": 0.60,
                    "breakout": 0.65,
                    "volatility_swing": 0.85,
                },
                {
                    "mean_reversion": 1.40,
                    "trend": 0.55,
                    "momentum": 0.60,
                    "volatility": 0.90,
                    "fundamental": 1.10,
                    "sentiment": 0.90,
                    "macro": 0.90,
                },
            )

        elif regime == MarketRegimeType.HIGH_VOLATILITY:
            return (
                ["mean_reversion", "volatility_swing"],
                {
                    "volatility_swing": 1.30,
                    "mean_reversion": 1.20,
                    "trend_following": 0.60,
                    "momentum": 0.50,
                    "breakout": 0.50,
                    "pullback": 0.60,
                },
                {
                    "volatility": 1.40,
                    "mean_reversion": 1.20,
                    "trend": 0.60,
                    "momentum": 0.50,
                    "fundamental": 1.00,
                    "sentiment": 0.80,
                    "macro": 1.20,
                },
            )

        elif regime == MarketRegimeType.LOW_VOLATILITY:
            return (
                ["breakout", "momentum", "trend_following"],
                {
                    "breakout": 1.35,
                    "momentum": 1.25,
                    "trend_following": 1.15,
                    "pullback": 1.05,
                    "mean_reversion": 0.70,
                    "volatility_swing": 1.10,
                },
                {
                    "trend": 1.20,
                    "momentum": 1.25,
                    "volatility": 1.10,
                    "mean_reversion": 0.70,
                    "fundamental": 1.00,
                    "sentiment": 1.00,
                    "macro": 1.00,
                },
            )

        else:  # UNCERTAIN
            return (
                ["mean_reversion"],
                {
                    "trend_following": 0.50,
                    "momentum": 0.50,
                    "mean_reversion": 0.60,
                    "breakout": 0.40,
                    "pullback": 0.50,
                    "volatility_swing": 0.50,
                },
                {
                    "trend": 0.50,
                    "momentum": 0.50,
                    "mean_reversion": 0.60,
                    "volatility": 0.50,
                    "fundamental": 0.80,
                    "sentiment": 0.50,
                    "macro": 0.50,
                },
            )


regime_detector = MarketRegimeDetector()
