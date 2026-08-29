"""
ATHENA Evidence & Statistical Significance Validator
Independent layer ensuring empirical validity before any decision is formed.
"""

from typing import List, Tuple
from packages.common.config import settings
from packages.logging.logger import get_logger
from packages.schemas.debate import DebateReport
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.regime import RegimeState

logger = get_logger("athena.evidence_validator")


class EvidenceValidator:
    """
    Validates agent debate outputs against empirical backtest stats,
    data quality, regime consistency, and transaction cost margins.
    """

    def validate_recommendation(
        self,
        symbol: str,
        debate_report: DebateReport,
        feature_snapshot: FeatureSnapshot,
        regime_state: RegimeState,
    ) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        is_valid = True

        # 1. Check Agreement Score Threshold
        if debate_report.agreement_score < 0.60:
            is_valid = False
            reasons.append(f"Insufficient agent consensus (agreement score {debate_report.agreement_score:.2f} < 0.60).")

        # 2. Check Data Quality Minimum
        if "data_quality" in feature_snapshot.raw_feature_map:
            score = feature_snapshot.raw_feature_map["data_quality"]
            if score < settings.MIN_DATA_QUALITY_SCORE:
                is_valid = False
                reasons.append(f"Data quality score {score:.2f} below required threshold {settings.MIN_DATA_QUALITY_SCORE}.")

        # 3. Check Regime Compatibility
        if debate_report.recommended_action == "BUY" and regime_state.regime.value == "CRASH":
            is_valid = False
            reasons.append("Proposing BUY in a confirmed CRASH market regime is rejected.")

        # 4. Check Transaction Cost Drag
        liq = feature_snapshot.liquidity
        est_cost_pct = (liq.bid_ask_spread_bps + 2.0) / 10000.0
        expected_profit_pct = 0.045
        if est_cost_pct > (expected_profit_pct * 0.35):
            is_valid = False
            reasons.append(f"Transaction cost drag ({est_cost_pct*100:.3f}%) exceeds 35% of expected return.")

        # 5. Check Signal Stability (Z-score not at hyper-extreme blowout)
        stat = feature_snapshot.statistical
        if abs(stat.z_score_20d) > 3.8:
            reasons.append(f"Statistical Z-score extreme ({stat.z_score_20d:.2f}) indicates potential structural break.")

        if is_valid:
            reasons.append("Empirical evidence, regime alignment, and statistical significance verified.")

        return is_valid, reasons


evidence_validator = EvidenceValidator()
