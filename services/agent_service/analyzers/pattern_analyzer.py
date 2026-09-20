"""
ATHENA V2 Pattern Analyzer (Non-Voting Analytical Module)
Provides geometric chart structure, volatility squeeze, and pivot analysis to TechnicalAgent.
"""

from typing import Any, Dict
from packages.schemas.feature import FeatureSnapshot


class PatternAnalyzer:
    """Evaluates candlestick price structures and volatility boundaries."""

    def analyze_patterns(self, features: FeatureSnapshot) -> Dict[str, Any]:
        tech = features.technical
        price = features.current_price

        patterns = []
        is_consolidation = tech.bb_bandwidth < 0.05
        if is_consolidation:
            patterns.append("Bollinger Band Volatility Compression")

        is_near_support = abs(price - tech.pivot_support) / max(price, 1.0) < 0.015 if price > 0 else False
        is_near_resistance = abs(price - tech.pivot_resistance) / max(price, 1.0) < 0.015 if price > 0 else False

        is_breakout = price >= tech.pivot_resistance and tech.volume_ratio >= 1.20 if price > 0 else False
        is_pullback = tech.ema_9 > tech.ema_21 and abs(price - tech.ema_21) / max(price, 1.0) < 0.015 if price > 0 else False

        if is_near_support:
            patterns.append("Support Level Rebound Setup")
        if is_near_resistance:
            patterns.append("Resistance Breakout Pressure")
        if is_breakout:
            patterns.append("Pivot Resistance Breakout")
        if is_pullback:
            patterns.append("21 EMA Retracement Support")

        trend_structure = "UPTREND" if tech.ema_50 > tech.ema_200 and price > tech.ema_50 else (
            "DOWNTREND" if tech.ema_50 < tech.ema_200 and price < tech.ema_50 else "CONSOLIDATION"
        )

        return {
            "patterns_detected": patterns,
            "trend_structure": trend_structure,
            "is_volatility_squeeze": is_consolidation,
            "is_breakout_candidate": is_breakout,
            "is_pullback_candidate": is_pullback,
            "dist_to_support_pct": round((price - tech.pivot_support) / max(price, 1.0) * 100, 2) if price > 0 else 0.0,
            "dist_to_resistance_pct": round((tech.pivot_resistance - price) / max(price, 1.0) * 100, 2) if price > 0 else 0.0,
        }

    def analyze_pattern(self, features: FeatureSnapshot) -> Dict[str, Any]:
        """Alias for analyze_patterns."""
        return self.analyze_patterns(features)


pattern_analyzer = PatternAnalyzer()
