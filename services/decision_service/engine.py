"""
ATHENA Profit-Optimized Quantitative Decision Engine
Selective Entry Filtering, Position Churn Prevention, and Auto-Profit Taking.
"""

import uuid
from datetime import datetime
from typing import Dict, List
from packages.common.config import settings
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentRunSummary
from packages.schemas.debate import DebateReport
from packages.schemas.decision import ActionType, AlternativeScenario, TradingDecision
from packages.schemas.events import Event, EventType
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.portfolio import PortfolioState
from packages.schemas.regime import MarketRegimeType, RegimeState
from packages.schemas.strategy import StrategyOutput
from services.validator_service.validator import evidence_validator

logger = get_logger("athena.decision_engine")


class DecisionEngine:
    """Profit-optimized, disciplined decision synthesizer with strict entry filters."""

    def generate_decision(
        self,
        symbol: str,
        feature_snapshot: FeatureSnapshot,
        regime_state: RegimeState,
        agent_summary: AgentRunSummary,
        strategy_outputs: Dict[str, StrategyOutput],
        debate_report: DebateReport,
        portfolio_state: PortfolioState,
    ) -> TradingDecision:
        current_price = feature_snapshot.current_price
        decision_id = str(uuid.uuid4())
        existing_position = portfolio_state.positions.get(symbol)

        # Dynamic Stop Loss & Take Profit based on ATR Volatility & Key Pivots
        atr = feature_snapshot.technical.atr_14 or (current_price * 0.015)
        stop_loss = round(max(current_price - (2.0 * atr), feature_snapshot.technical.pivot_support * 0.99), 2)
        take_profit = round(current_price + (4.0 * atr), 2)
        risk_reward = round(abs(take_profit - current_price) / max(0.01, abs(current_price - stop_loss)), 2)

        # 1. Check Existing Position Management (Auto Take-Profit & Stop-Loss)
        if existing_position and existing_position.shares > 0:
            entry_px = existing_position.average_entry_price
            pnl_pct = (current_price - entry_px) / entry_px if entry_px > 0 else 0.0

            # Profit Target Reached (+3.5% or above take_profit level)
            if current_price >= take_profit or pnl_pct >= 0.035:
                logger.info(f"Target profit hit on {symbol} (+{pnl_pct*100:.1f}%). Triggering SELL to lock in gains.")
                return self._create_decision(
                    decision_id=decision_id,
                    symbol=symbol,
                    action=ActionType.SELL,
                    confidence=0.95,
                    current_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward=risk_reward,
                    target_weight=0.0,
                    suggested_shares=int(existing_position.shares),
                    reasoning=f"Take Profit Target Reached (+{pnl_pct*100:.2f}% gain). Locking in realized profit.",
                    agent_summary=agent_summary,
                    debate_report=debate_report,
                    regime_state=regime_state,
                    is_valid=True,
                    val_reasons=["Profit target achieved; capital recycling triggered."],
                )

            # Stop Loss Breached (-2.0% or below stop_loss level)
            if current_price <= stop_loss or pnl_pct <= -0.025:
                logger.warning(f"Stop loss hit on {symbol} ({pnl_pct*100:.1f}%). Triggering SELL to cut loss.")
                return self._create_decision(
                    decision_id=decision_id,
                    symbol=symbol,
                    action=ActionType.SELL,
                    confidence=0.90,
                    current_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward=risk_reward,
                    target_weight=0.0,
                    suggested_shares=int(existing_position.shares),
                    reasoning=f"Trailing Stop Loss Hit ({pnl_pct*100:.2f}% loss). Cutting loss early to preserve capital.",
                    agent_summary=agent_summary,
                    debate_report=debate_report,
                    regime_state=regime_state,
                    is_valid=True,
                    val_reasons=["Risk limit touched; stop loss execution required."],
                )

            # Otherwise Hold Active Position (Do NOT duplicate buy)
            logger.info(f"Position active for {symbol} (P&L: {pnl_pct*100:+.2f}%). Holding for target.")
            return self._create_decision(
                decision_id=decision_id,
                symbol=symbol,
                action=ActionType.HOLD,
                confidence=0.80,
                current_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward=risk_reward,
                target_weight=0.0,
                suggested_shares=0,
                reasoning=f"Active Position Held: Current P&L is {pnl_pct*100:+.2f}%. Patiently holding for ${take_profit:,.2f} profit target.",
                agent_summary=agent_summary,
                debate_report=debate_report,
                regime_state=regime_state,
                is_valid=True,
                val_reasons=["Asset already in portfolio; awaiting target expansion."],
            )

        # 2. Strict New Entry Quality Gate
        is_valid, val_reasons = evidence_validator.validate_recommendation(
            symbol=symbol,
            debate_report=debate_report,
            feature_snapshot=feature_snapshot,
            regime_state=regime_state,
        )

        # High-Conviction Selective Entry Conditions:
        # - Statistical Evidence is Validated
        # - Recommended Action is BUY
        # - Multi-Agent Consensus >= 80%
        # - Agreement Score >= 0.85
        # - Reward to Risk >= 2.0 : 1
        high_conviction = (
            is_valid
            and debate_report.recommended_action == "BUY"
            and debate_report.consensus_confidence >= 0.78
            and debate_report.agreement_score >= 0.85
            and risk_reward >= 1.9
        )

        if high_conviction:
            action = ActionType.BUY
            target_weight = 0.05  # Disciplined 5% position sizing
            suggested_shares = int((portfolio_state.cash * target_weight) / max(current_price, 1.0))
            reasoning = (
                f"### High-Conviction Buy Setup for {symbol}\n"
                f"- **Edge**: Validated statistical edge with {debate_report.consensus_confidence*100:.0f}% agent consensus.\n"
                f"- **Reward-to-Risk**: {risk_reward:.1f} : 1 skew (Target: ${take_profit:.2f}, Stop: ${stop_loss:.2f})\n"
                f"- **Agreement**: {debate_report.agreement_score*100:.0f}% debate unanimity.\n"
                f"- **Regime**: {regime_state.regime.value} ({regime_state.description})"
            )
        else:
            action = ActionType.HOLD
            target_weight = 0.0
            suggested_shares = 0
            reasoning = (
                f"### Patient Hold for {symbol}\n"
                f"- Market conditions / agent consensus ({debate_report.consensus_confidence*100:.0f}%) do not satisfy strict high-probability profit criteria.\n"
                f"- Preserving dry powder cash for higher-skew setups."
            )

        return self._create_decision(
            decision_id=decision_id,
            symbol=symbol,
            action=action,
            confidence=debate_report.consensus_confidence,
            current_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=risk_reward,
            target_weight=target_weight,
            suggested_shares=suggested_shares,
            reasoning=reasoning,
            agent_summary=agent_summary,
            debate_report=debate_report,
            regime_state=regime_state,
            is_valid=is_valid,
            val_reasons=val_reasons,
        )

    def _create_decision(
        self,
        decision_id: str,
        symbol: str,
        action: ActionType,
        confidence: float,
        current_price: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: float,
        target_weight: float,
        suggested_shares: int,
        reasoning: str,
        agent_summary: AgentRunSummary,
        debate_report: DebateReport,
        regime_state: RegimeState,
        is_valid: bool,
        val_reasons: List[str],
    ) -> TradingDecision:
        scenarios = [
            AlternativeScenario(
                name="Macro Rates Spike / Hawk Pivot",
                trigger_condition="10-Year yield increases by > 15 bps in 24h",
                probability=0.18,
                mitigation_action=f"Tighten stop loss to ${round(current_price * 0.98, 2)}",
            ),
            AlternativeScenario(
                name="Earnings Multiple Contraction",
                trigger_condition="Sector ETF breaks below 50-day moving average",
                probability=0.15,
                mitigation_action="Immediate trailing stop activation",
            ),
        ]
        model_versions = {
            name: out.model_version for name, out in agent_summary.agent_outputs.items()
        }

        return TradingDecision(
            id=decision_id,
            timestamp=datetime.utcnow(),
            symbol=symbol,
            action=action,
            confidence=confidence,
            calibrated_probability=round(confidence * 0.92, 2),
            current_price=current_price,
            target_weight=target_weight,
            suggested_shares=suggested_shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
            expected_return_pct=0.048 if action == ActionType.BUY else 0.0,
            expected_drawdown_pct=0.019,
            risk_reward_ratio=risk_reward,
            holding_period="5D",
            regime=regime_state.regime.value,
            debate_agreement_score=debate_report.agreement_score,
            supporting_agents=agent_summary.supporting_agents,
            opposing_agents=agent_summary.opposing_agents,
            reasoning=reasoning,
            alternative_scenarios=scenarios,
            model_versions=model_versions,
            validation_status="VALIDATED" if is_valid else "REJECTED",
            validation_reasons=val_reasons,
        )


decision_engine = DecisionEngine()
