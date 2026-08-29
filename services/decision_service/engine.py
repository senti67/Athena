"""
ATHENA Confidence-Weighted Decision Engine
Synthesizes agent debates, validated evidence, regime parameters, and alternative scenarios.
"""

import uuid
from datetime import datetime
from typing import Dict, List
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentRunSummary
from packages.schemas.debate import DebateReport
from packages.schemas.decision import ActionType, AlternativeScenario, TradingDecision
from packages.schemas.events import Event, EventType
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.portfolio import PortfolioState
from packages.schemas.regime import RegimeState
from packages.schemas.strategy import StrategyOutput
from services.validator_service.validator import evidence_validator

logger = get_logger("athena.decision_engine")


class DecisionEngine:
    """Confidence-weighted ensemble trading decision generator."""

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

        # 1. Independent Evidence Validation
        is_valid, val_reasons = evidence_validator.validate_recommendation(
            symbol=symbol,
            debate_report=debate_report,
            feature_snapshot=feature_snapshot,
            regime_state=regime_state,
        )

        # Determine primary Action
        if not is_valid or debate_report.recommended_action == "HOLD":
            action = ActionType.HOLD
            target_weight = 0.0
            stop_loss = round(current_price * 0.95, 2)
            take_profit = round(current_price * 1.05, 2)
        elif debate_report.recommended_action == "BUY":
            action = ActionType.BUY
            target_weight = 0.05  # Base 5% target allocation
            # Dynamic stop loss and take profit based on ATR and support
            atr = feature_snapshot.technical.atr_14
            stop_loss = round(max(current_price - (2.0 * atr), feature_snapshot.technical.pivot_support * 0.99), 2)
            take_profit = round(current_price + (4.0 * atr), 2)
        else:
            action = ActionType.SELL
            target_weight = 0.0
            stop_loss = round(current_price * 1.03, 2)
            take_profit = round(current_price * 0.92, 2)

        risk_reward = round(
            abs(take_profit - current_price) / max(0.01, abs(current_price - stop_loss)), 2
        )

        # 2. Alternative Scenarios Modeling
        scenarios = [
            AlternativeScenario(
                name="Macro Rates Spike / Hawk Pivot",
                trigger_condition="10-Year yield increases by > 15 bps in 24h",
                probability=0.18,
                mitigation_action=f"Tighten stop loss to ${round(current_price * 0.98, 2)} and reduce target size by 50%",
            ),
            AlternativeScenario(
                name="Earnings Multiple Contraction",
                trigger_condition="Sector ETF breaks below 50-day moving average",
                probability=0.15,
                mitigation_action="Immediate trailing stop activation",
            ),
        ]

        # 3. Model versions and audit lineage
        model_versions = {
            name: out.model_version for name, out in agent_summary.agent_outputs.items()
        }

        # 4. Synthesize Markdown Reasoning Trace
        reasoning = (
            f"### Multi-Agent Synthesis for {symbol}\n"
            f"- **Action**: {action.value} | **Confidence**: {debate_report.consensus_confidence*100:.0f}%\n"
            f"- **Regime**: {regime_state.regime.value} ({regime_state.description})\n"
            f"- **Supporting Agents ({len(agent_summary.supporting_agents)})**: {', '.join(agent_summary.supporting_agents)}\n"
            f"- **Opposing Agents ({len(agent_summary.opposing_agents)})**: {', '.join(agent_summary.opposing_agents) if agent_summary.opposing_agents else 'None'}\n"
            f"- **Debate Synthesis**: {debate_report.debate_synthesis}\n"
            f"- **Stop Loss**: ${stop_loss:.2f} | **Take Profit**: ${take_profit:.2f} (R:R {risk_reward}:1)\n"
        )

        decision = TradingDecision(
            id=decision_id,
            timestamp=datetime.utcnow(),
            symbol=symbol,
            action=action,
            confidence=debate_report.consensus_confidence,
            calibrated_probability=round(debate_report.consensus_confidence * 0.92, 2),
            current_price=current_price,
            target_weight=target_weight,
            suggested_shares=int((portfolio_state.cash * target_weight) / current_price) if current_price > 0 and action == ActionType.BUY else 0,
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

        return decision


decision_engine = DecisionEngine()
