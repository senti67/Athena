"""
ATHENA Quantitative Market Regime Schemas
Defines the 6 core market regime classifications, metrics breakdowns, and strategy/feature suitability matrices.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MarketRegimeType(str, Enum):
    """The 6 Core Market Regime Classifications."""
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    UNCERTAIN = "UNCERTAIN"

    # Backward compatibility aliases
    BULL = "TRENDING_BULL"
    BEAR = "TRENDING_BEAR"
    RECOVERY = "TRENDING_BULL"
    CRASH = "HIGH_VOLATILITY"
    CORRECTION = "TRENDING_BEAR"


class RegimeMetrics(BaseModel):
    adx_14: float = 20.0
    atr_pct: float = 0.015
    ema_trend_score: float = 0.0      # +1.0 for perfect bullish stack, -1.0 for bearish
    ema_slope_20: float = 0.0         # Rate of change of EMA 21
    realized_vol_20d: float = 0.18
    vol_ratio: float = 1.0            # Realized vol / baseline
    bb_bandwidth: float = 0.04
    volume_ratio: float = 1.0
    benchmark_trend: str = "NEUTRAL"  # BULLISH / BEARISH / NEUTRAL


class RegimeEnsembleBreakdown(BaseModel):
    """Legacy breakdown for compatibility."""
    hmm_regime: MarketRegimeType = MarketRegimeType.TRENDING_BULL
    hmm_confidence: float = 0.85
    gmm_clustering_regime: MarketRegimeType = MarketRegimeType.TRENDING_BULL
    gmm_confidence: float = 0.80
    volatility_trend_regime: MarketRegimeType = MarketRegimeType.TRENDING_BULL
    volatility_trend_confidence: float = 0.90
    classifier_regime: MarketRegimeType = MarketRegimeType.TRENDING_BULL
    classifier_confidence: float = 0.82


class RegimeState(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol_or_market: str = "SPY"
    regime: MarketRegimeType = MarketRegimeType.TRENDING_BULL
    confidence: float = Field(ge=0.0, le=1.0, default=0.75)
    description: str = "Trending bullish regime with positive moving average slope and expanding momentum."
    recommended_strategies: List[str] = Field(
        default_factory=lambda: ["trend_following", "momentum", "breakout", "pullback"]
    )
    strategy_suitability_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "trend_following": 1.35,
            "momentum": 1.30,
            "breakout": 1.20,
            "pullback": 1.15,
            "mean_reversion": 0.50,
            "volatility_swing": 0.60,
        }
    )
    feature_group_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "trend": 1.30,
            "momentum": 1.25,
            "mean_reversion": 0.50,
            "volatility": 0.80,
            "fundamental": 1.00,
            "sentiment": 1.00,
            "macro": 1.10,
        }
    )
    metrics: RegimeMetrics = Field(default_factory=RegimeMetrics)
    ensemble_breakdown: RegimeEnsembleBreakdown = Field(default_factory=RegimeEnsembleBreakdown)
