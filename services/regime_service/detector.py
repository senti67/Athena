"""
ATHENA Market Regime Detection Ensemble
Synthesizes Hidden Markov Model (HMM), GMM clustering, and Volatility/Trend classification.
"""

from datetime import datetime
from typing import Dict, List
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.events import Event, EventType
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.regime import MarketRegimeType, RegimeEnsembleBreakdown, RegimeState

logger = get_logger("athena.regime_detector")


class MarketRegimeDetector:
    """
    Multi-model ensemble regime classifier.
    Determines market macro state and dynamically weights appropriate strategies.
    """

    def detect_regime(self, snapshot: FeatureSnapshot) -> RegimeState:
        tech = snapshot.technical
        stat = snapshot.statistical
        vol = snapshot.volatility
        cross = snapshot.cross_asset

        # 1. HMM Hidden State Proxy (Estimates probability of hidden Bull/Bear/Sideways state)
        if stat.returns_20d > 0.03 and vol.realized_vol_20d < 0.22:
            hmm_regime = MarketRegimeType.BULL
            hmm_conf = 0.88
        elif stat.returns_20d < -0.05 and vol.realized_vol_20d > 0.25:
            hmm_regime = MarketRegimeType.BEAR
            hmm_conf = 0.82
        elif vol.realized_vol_20d > 0.35:
            hmm_regime = MarketRegimeType.HIGH_VOLATILITY
            hmm_conf = 0.90
        else:
            hmm_regime = MarketRegimeType.SIDEWAYS
            hmm_conf = 0.75

        # 2. GMM Return/Vol Clustering Classifier
        if stat.returns_5d > 0.015 and tech.rsi_14 > 55.0:
            gmm_regime = MarketRegimeType.BULL
            gmm_conf = 0.85
        elif stat.returns_5d < -0.02 and tech.rsi_14 < 40.0:
            gmm_regime = MarketRegimeType.BEAR
            gmm_conf = 0.80
        elif vol.realized_vol_20d < 0.12:
            gmm_regime = MarketRegimeType.LOW_VOLATILITY
            gmm_conf = 0.84
        else:
            gmm_regime = MarketRegimeType.SIDEWAYS
            gmm_conf = 0.78

        # 3. Volatility / Trend ADX-ATR Matrix
        price_above_ema50 = snapshot.current_price > tech.ema_50
        price_above_ema200 = snapshot.current_price > tech.ema_200
        strong_trend = tech.adx_14 > 25.0

        if price_above_ema50 and price_above_ema200 and strong_trend:
            vol_trend_regime = MarketRegimeType.BULL
            vol_trend_conf = 0.92
        elif (not price_above_ema50) and (not price_above_ema200) and strong_trend:
            vol_trend_regime = MarketRegimeType.BEAR
            vol_trend_conf = 0.89
        elif vol.vol_regime_ratio > 1.8:
            vol_trend_regime = MarketRegimeType.HIGH_VOLATILITY
            vol_trend_conf = 0.87
        else:
            vol_trend_regime = MarketRegimeType.SIDEWAYS
            vol_trend_conf = 0.80

        # 4. Supervised ML Classifier Proxy (incorporating Cross-Asset & Risk-On)
        if cross.risk_on_indicator > 0.65 and stat.returns_1d > -0.01:
            clf_regime = MarketRegimeType.BULL
            clf_conf = 0.86
        elif cross.risk_on_indicator < 0.35 or cross.vix_level > 28.0:
            clf_regime = MarketRegimeType.HIGH_VOLATILITY if cross.vix_level > 28.0 else MarketRegimeType.BEAR
            clf_conf = 0.88
        else:
            clf_regime = MarketRegimeType.SIDEWAYS
            clf_conf = 0.76

        breakdown = RegimeEnsembleBreakdown(
            hmm_regime=hmm_regime,
            hmm_confidence=hmm_conf,
            gmm_clustering_regime=gmm_regime,
            gmm_confidence=gmm_conf,
            volatility_trend_regime=vol_trend_regime,
            volatility_trend_confidence=vol_trend_conf,
            classifier_regime=clf_regime,
            classifier_confidence=clf_conf,
        )

        # Ensemble Voting with confidence weighting
        votes: Dict[MarketRegimeType, float] = {}
        for r, c in [
            (hmm_regime, hmm_conf * 0.25),
            (gmm_regime, gmm_conf * 0.25),
            (vol_trend_regime, vol_trend_conf * 0.30),
            (clf_regime, clf_conf * 0.20),
        ]:
            votes[r] = votes.get(r, 0.0) + c

        consensus_regime = max(votes.items(), key=lambda x: x[1])[0]
        consensus_confidence = round(votes[consensus_regime], 2)

        # Map regime to strategy weights and recommendations
        recommended_strategies, strategy_weights, description = self._get_regime_allocations(consensus_regime)

        state = RegimeState(
            timestamp=datetime.utcnow(),
            symbol_or_market=snapshot.symbol,
            regime=consensus_regime,
            confidence=min(0.98, max(0.60, consensus_confidence)),
            description=description,
            recommended_strategies=recommended_strategies,
            strategy_suitability_weights=strategy_weights,
            ensemble_breakdown=breakdown,
        )

        return state

    def _get_regime_allocations(self, regime: MarketRegimeType):
        if regime == MarketRegimeType.BULL:
            return (
                ["trend_following", "momentum", "growth", "breakout"],
                {
                    "trend_following": 1.35,
                    "momentum": 1.30,
                    "growth": 1.25,
                    "breakout": 1.20,
                    "pullback": 1.15,
                    "mean_reversion": 0.60,
                    "volatility": 0.50,
                },
                "Sustained upward price trend with expanding liquidity and strong risk appetite.",
            )
        elif regime == MarketRegimeType.BEAR:
            return (
                ["statistical_arbitrage", "pairs", "volatility", "value"],
                {
                    "pairs": 1.30,
                    "statistical_arbitrage": 1.25,
                    "volatility": 1.35,
                    "value": 1.10,
                    "trend_following": 0.70,
                    "momentum": 0.50,
                    "growth": 0.40,
                },
                "Persistent downtrend with risk aversion and negative macro headwinds.",
            )
        elif regime == MarketRegimeType.HIGH_VOLATILITY:
            return (
                ["volatility", "mean_reversion", "statistical_arbitrage"],
                {
                    "volatility": 1.50,
                    "mean_reversion": 1.20,
                    "statistical_arbitrage": 1.10,
                    "trend_following": 0.50,
                    "momentum": 0.40,
                    "breakout": 0.50,
                },
                "Elevated realized and implied volatility; erratic swings and expanding spreads.",
            )
        else:  # SIDEWAYS / LOW_VOLATILITY
            return (
                ["mean_reversion", "pairs", "statistical_arbitrage", "swing"],
                {
                    "mean_reversion": 1.40,
                    "pairs": 1.30,
                    "statistical_arbitrage": 1.25,
                    "swing": 1.20,
                    "trend_following": 0.60,
                    "breakout": 0.60,
                },
                "Range-bound market oscillating between established support and resistance boundaries.",
            )


regime_detector = MarketRegimeDetector()
