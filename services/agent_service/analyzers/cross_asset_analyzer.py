"""
ATHENA V2 Cross-Asset Analyzer (Non-Voting Analytical Module)
Provides intermarket context, broad market index trends, and risk-on/risk-off environment.
"""

from typing import Any, Dict, Optional
from packages.schemas.feature import FeatureSnapshot


class CrossAssetAnalyzer:
    """Extracts broad market macro context and cross-asset confirmation."""

    def analyze_cross_asset(
        self, features: FeatureSnapshot, extra_indicators: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        cross = features.cross_asset
        vix = cross.vix_level if cross and cross.vix_level > 0 else 18.0
        risk_on = cross.risk_on_indicator if cross and cross.risk_on_indicator > 0 else 0.50

        # Market climate interpretation
        if vix > 25.0:
            climate = "HIGH_FEAR_VOLATILITY"
        elif vix < 15.0 and risk_on > 0.60:
            climate = "CALM_RISK_ON"
        else:
            climate = "NEUTRAL_NORMAL"

        return {
            "market_climate": climate,
            "vix_level": vix,
            "risk_on_indicator": risk_on,
            "is_risk_on": risk_on >= 0.55,
        }


cross_asset_analyzer = CrossAssetAnalyzer()
