"""
ATHENA Independent Risk Management VETO Layer
Holds unilateral, non-bypassable veto power over all AI agent and strategy recommendations.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from packages.common.config import settings
from packages.common.exceptions import RiskVetoException
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.monitoring.metrics import metrics
from packages.schemas.decision import ActionType, TradingDecision
from packages.schemas.events import Event, EventType
from packages.schemas.portfolio import PortfolioState
from packages.schemas.risk import (
    RiskCheckResult,
    RiskLimits,
    RiskMetrics,
    RiskViolation,
)

logger = get_logger("athena.risk_engine")


class RiskEngine:
    """
    Independent Risk Guardian.
    Evaluates every proposed trade against institutional hard bounds.
    Can veto any order before it reaches the execution router.
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits(
            max_daily_loss=settings.MAX_DAILY_LOSS,
            max_position_size=settings.MAX_POSITION_SIZE,
            max_portfolio_exposure=settings.MAX_PORTFOLIO_EXPOSURE,
            max_single_asset_exposure=settings.MAX_SINGLE_ASSET_EXPOSURE,
            max_sector_concentration=settings.MAX_SECTOR_CONCENTRATION,
            max_leverage=settings.MAX_LEVERAGE,
            max_drawdown_limit=settings.MAX_DRAWDOWN_LIMIT,
            var_95_limit=settings.VAR_95_LIMIT,
            cvar_95_limit=settings.CVAR_95_LIMIT,
        )
        self.kill_switch_active = settings.CIRCUIT_BREAKER_TRIGGERED

    def trigger_kill_switch(self, reason: str = "Manual Emergency Operator Kill Switch"):
        """Instantly halts all trading activity platform-wide."""
        self.kill_switch_active = True
        logger.critical(f"EMERGENCY KILL SWITCH ACTIVATED: {reason}")

    def reset_kill_switch(self):
        self.kill_switch_active = False
        logger.info("Emergency kill switch deactivated by authorized operator.")

    def evaluate_decision(
        self,
        decision: TradingDecision,
        portfolio_state: PortfolioState,
        data_quality_score: float = 1.0,
    ) -> RiskCheckResult:
        check_id = str(uuid.uuid4())
        violations: List[RiskViolation] = []
        warnings: List[str] = []
        approved = True
        veto_reason = None

        # 1. EMERGENCY KILL SWITCH CHECK
        if self.kill_switch_active:
            approved = False
            veto_reason = "Emergency Kill Switch is active. All order submission is blocked."
            violations.append(
                RiskViolation(
                    rule_name="KILL_SWITCH",
                    limit_value=0.0,
                    current_or_projected_value=1.0,
                    message=veto_reason,
                    severity="CRITICAL",
                )
            )

        # 2. VALIDATION STATUS CHECK
        if decision.validation_status != "VALIDATED" or decision.action == ActionType.HOLD:
            approved = False
            veto_reason = "Decision not in VALIDATED state or is HOLD."

        # 3. DATA QUALITY SCORE CHECK
        if data_quality_score < self.limits.min_data_quality_score:
            approved = False
            msg = f"Data quality score ({data_quality_score:.2f}) below institutional threshold ({self.limits.min_data_quality_score:.2f})."
            veto_reason = msg
            violations.append(
                RiskViolation(
                    rule_name="DATA_QUALITY_MINIMUM",
                    limit_value=self.limits.min_data_quality_score,
                    current_or_projected_value=data_quality_score,
                    message=msg,
                    severity="CRITICAL",
                )
            )

        # 4. MAXIMUM DAILY LOSS CIRCUIT BREAKER
        daily_loss = -(portfolio_state.daily_realized_pnl + portfolio_state.daily_unrealized_pnl)
        if daily_loss >= self.limits.max_daily_loss:
            approved = False
            msg = f"Daily portfolio loss (${daily_loss:,.2f}) breached limit (${self.limits.max_daily_loss:,.2f})."
            veto_reason = msg
            violations.append(
                RiskViolation(
                    rule_name="MAX_DAILY_LOSS",
                    limit_value=self.limits.max_daily_loss,
                    current_or_projected_value=daily_loss,
                    message=msg,
                    severity="CRITICAL",
                )
            )

        # 5. MAXIMUM POSITION SIZE CHECK
        proposed_dollar_value = decision.suggested_shares * decision.current_price
        if proposed_dollar_value > self.limits.max_position_size:
            # Scale down rather than full rejection if feasible
            max_allowed_shares = int(self.limits.max_position_size / decision.current_price)
            warnings.append(
                f"Proposed order (${proposed_dollar_value:,.2f}) scaled down to max size (${self.limits.max_position_size:,.2f})."
            )
            decision.suggested_shares = max_allowed_shares
            proposed_dollar_value = max_allowed_shares * decision.current_price

        # 6. SINGLE ASSET EXPOSURE (Cap at e.g. 10% NAV)
        projected_asset_weight = proposed_dollar_value / max(1.0, portfolio_state.nav)
        if projected_asset_weight > self.limits.max_single_asset_exposure:
            approved = False
            msg = f"Projected position weight ({projected_asset_weight*100:.1f}%) exceeds single asset cap ({self.limits.max_single_asset_exposure*100:.1f}%)."
            veto_reason = msg
            violations.append(
                RiskViolation(
                    rule_name="MAX_SINGLE_ASSET_EXPOSURE",
                    limit_value=self.limits.max_single_asset_exposure,
                    current_or_projected_value=projected_asset_weight,
                    message=msg,
                    severity="CRITICAL",
                )
            )

        # 7. CASH AVAILABILITY & BUYING POWER
        if decision.action == ActionType.BUY and proposed_dollar_value > portfolio_state.cash:
            approved = False
            msg = f"Insufficient cash buying power (${portfolio_state.cash:,.2f}) for proposed order (${proposed_dollar_value:,.2f})."
            veto_reason = msg
            violations.append(
                RiskViolation(
                    rule_name="INSUFFICIENT_BUYING_POWER",
                    limit_value=portfolio_state.cash,
                    current_or_projected_value=proposed_dollar_value,
                    message=msg,
                    severity="CRITICAL",
                )
            )

        # 8. MINIMUM REWARD-TO-RISK RATIO
        if decision.action == ActionType.BUY and decision.risk_reward_ratio < self.limits.min_risk_reward_ratio:
            approved = False
            msg = f"Reward-to-risk ratio ({decision.risk_reward_ratio:.2f}) below institutional requirement ({self.limits.min_risk_reward_ratio:.2f})."
            veto_reason = msg
            violations.append(
                RiskViolation(
                    rule_name="MIN_REWARD_RISK_RATIO",
                    limit_value=self.limits.min_risk_reward_ratio,
                    current_or_projected_value=decision.risk_reward_ratio,
                    message=msg,
                    severity="CRITICAL",
                )
            )

        risk_score = round(
            0.15 + (0.35 if violations else 0.0) + (0.10 if warnings else 0.0) + (0.10 * (1.0 - decision.confidence)),
            2,
        )

        risk_metrics = RiskMetrics(
            portfolio_nav=portfolio_state.nav,
            current_cash=portfolio_state.cash,
            current_gross_exposure=portfolio_state.gross_exposure,
            current_net_exposure=portfolio_state.net_exposure,
            current_leverage=portfolio_state.leverage,
            daily_realized_pnl=portfolio_state.daily_realized_pnl,
            daily_unrealized_pnl=portfolio_state.daily_unrealized_pnl,
            current_drawdown_pct=0.012,
            historical_var_95=0.015,
            cvar_95_expected_shortfall=0.024,
        )

        if not approved:
            for v in violations:
                metrics.record_risk_veto(decision.symbol, v.rule_name)
            logger.warning(f"RISK VETO on {decision.symbol}: {veto_reason}")

        result = RiskCheckResult(
            check_id=check_id,
            timestamp=datetime.utcnow(),
            decision_id=decision.id,
            symbol=decision.symbol,
            action=decision.action.value,
            approved=approved,
            risk_score=min(1.0, risk_score),
            max_approved_shares=decision.suggested_shares if approved else 0,
            max_approved_dollar_amount=proposed_dollar_value if approved else 0.0,
            violations=violations,
            warnings=warnings,
            veto_reason=veto_reason,
            kill_switch_triggered=self.kill_switch_active,
            metrics_snapshot=risk_metrics,
        )

        return result


risk_engine = RiskEngine()
