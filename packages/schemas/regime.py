"""
ATHENA Market Regime Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MarketRegimeType(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    RECOVERY = "RECOVERY"
    CRASH = "CRASH"
    CORRECTION = "CORRECTION"


class RegimeEnsembleBreakdown(BaseModel):
    hmm_regime: MarketRegimeType = MarketRegimeType.BULL
    hmm_confidence: float = 0.85
    gmm_clustering_regime: MarketRegimeType = MarketRegimeType.BULL
    gmm_confidence: float = 0.80
    volatility_trend_regime: MarketRegimeType = MarketRegimeType.BULL
    volatility_trend_confidence: float = 0.90
    classifier_regime: MarketRegimeType = MarketRegimeType.BULL
    classifier_confidence: float = 0.82


class RegimeState(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol_or_market: str = "SPY"
    regime: MarketRegimeType = MarketRegimeType.BULL
    confidence: float = Field(ge=0.0, le=1.0, default=0.85)
    description: str = "Strong bullish regime with expanding breadth and subdued volatility"
    recommended_strategies: List[str] = Field(
        default_factory=lambda: ["trend_following", "momentum", "growth", "breakout"]
    )
    strategy_suitability_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "trend_following": 1.3,
            "momentum": 1.2,
            "mean_reversion": 0.6,
            "breakout": 1.2,
            "swing": 1.0,
            "volatility": 0.5,
        }
    )
    ensemble_breakdown: RegimeEnsembleBreakdown = Field(default_factory=RegimeEnsembleBreakdown)
