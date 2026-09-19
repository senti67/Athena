"""
ATHENA V2 Quantitative Decision Engine
Synthesizes Multi-Domain Research Consensus and Active Quantitative Strategy Setups,
verifies Transaction Costs, Compliance, and Risk, and produces fully-explained TradingDecisions.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from packages.common.config import settings
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentRunSummary
from packages.schemas.debate import DebateReport
from packages.schemas.decision import ActionType, AlternativeScenario, TradingDecision
from packages.schemas.events import Event, EventType
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.portfolio import PortfolioState
from packages.schemas.regime import RegimeState
from packages.schemas.strategy import StrategyOutput, StrategySignal
from services.validator_service.validator import evidence_validator
from services.risk_service.cost_analyzer import transaction_cost_analyzer
from services.risk_service.compliance import compliance_engine
from services.risk_service.position_sizer import position_sizer

logger = get_logger("athena.decision_engine")


class DecisionEngine:
    """
    Synthesizes research consensus, strategy setups, and risk guardrails into execution-ready decisions.
    """

    def generate_decision(
        self,
        symbol: str,
        feature_snapshot: FeatureSnapshot,
        regime_state: RegimeState,
        agent_summary: AgentRunSummary,
        strategy_outputs: Dict[str, StrategyOutput],
        debate_report: DebateReport,
        portfolio_state: PortfolioState,
        best_strategy_setup: Optional[StrategyOutput] = None,
    ) -> TradingDecision:
        current_price = feature_snapshot.current_price
        decision_id = str(uuid.uuid4())
        existing_position = portfolio_state.positions.get(symbol)

        # 1. ATR and Target / Stop Loss Levels
        atr = feature_snapshot.technical.atr_14 or (current_price * 0.015)
        stop_loss = round(max(current_price - (2.0 * atr), feature_snapshot.technical.pivot_support * 0.99), 2)
        take_profit = round(current_price + (4.0 * atr), 2)
        risk_reward = round(abs(take_profit - current_price) / max(0.01, abs(current_price - stop_loss)), 2)

        # 2. Existing Active Position Management (Exit rules)
        if existing_position and existing_position.shares > 0:
            entry_px = existing_position.average_entry_price
            pnl_pct = (current_price - entry_px) / entry_px if entry_px > 0 else 0.0

            # Profit Target Reached (+3.5% or above take_profit level)
            if current_price >= take_profit or pnl_pct >= 0.035:
                logger.info(f"Take Profit reached on {symbol} (+{pnl_pct*100:.1f}%). Triggering SELL.")
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
                    reasoning=f"Take Profit Target Reached (+{pnl_pct*100:.2f}% gain). Realizing gains and freeing capital.",
                    agent_summary=agent_summary,
                    debate_report=debate_report,
                    regime_state=regime_state,
                    is_valid=True,
                    val_reasons=["Profit target achieved; capital recycling triggered."],
                )

            # Stop Loss Breached (-2.5% or below stop_loss level)
            if current_price <= stop_loss or pnl_pct <= -0.025:
                logger.warning(f"Stop Loss hit on {symbol} ({pnl_pct*100:.1f}%). Triggering SELL.")
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
                    reasoning=f"Stop Loss Level Breached ({pnl_pct*100:.2f}% loss). Cutting loss to protect portfolio capital.",
                    agent_summary=agent_summary,
                    debate_report=debate_report,
                    regime_state=regime_state,
                    is_valid=True,
                    val_reasons=["Stop loss boundary reached."],
                )

            # Active position holding (prevent duplicate buying)
            logger.info(f"Position active for {symbol} (P&L: {pnl_pct*100:+.2f}%). Holding position.")
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
                reasoning=f"Active Position Held: Current P&L is {pnl_pct*100:+.2f}%. Holding for profit target ${take_profit:.2f}.",
                agent_summary=agent_summary,
                debate_report=debate_report,
                regime_state=regime_state,
                is_valid=True,
                val_reasons=["Asset already held; awaiting target expansion."],
            )

        # 3. New Entry Synthesis (Research Consensus + Active Strategy Setup)
        if best_strategy_setup is None:
            # Find the best setup from strategy_outputs
            valid_setups = [
                s for s in strategy_outputs.values()
                if s.signal == StrategySignal.BUY and s.is_active
            ]
            if valid_setups:
                valid_setups.sort(key=lambda s: (s.confidence, s.risk_reward), reverse=True)
                best_strategy_setup = valid_setups[0]

        # Validation & Compliance Pre-checks
        is_valid, val_reasons = evidence_validator.validate_recommendation(
            symbol=symbol,
            debate_report=debate_report,
            feature_snapshot=feature_snapshot,
            regime_state=regime_state,
        )

        comp_result = compliance_engine.check_compliance(symbol, current_price, "BUY")
        if not comp_result.is_compliant:
            is_valid = False
            val_reasons.extend(comp_result.violations)

        # Minimum thresholds
        min_res_conf = getattr(settings, "MIN_RESEARCH_CONFIDENCE", 0.65)
        min_res_agr = getattr(settings, "MIN_RESEARCH_AGREEMENT", 0.65)
        min_strat_conf = getattr(settings, "MIN_STRATEGY_CONFIDENCE", 0.65)
        agent_wt = getattr(settings, "AGENT_WEIGHT", 0.50)
        strat_wt = getattr(settings, "STRATEGY_WEIGHT", 0.50)

        has_consensus = (
            debate_report.recommended_action == "BUY"
            and debate_report.consensus_confidence >= min_res_conf
            and debate_report.agreement_score >= min_res_agr
        )

        has_strategy_setup = (
            best_strategy_setup is not None
            and best_strategy_setup.signal == StrategySignal.BUY
            and best_strategy_setup.confidence >= min_strat_conf
        )

        if is_valid and has_consensus and has_strategy_setup:
            # Synthesize combined confidence
            combined_conf = round(
                (agent_wt * debate_report.consensus_confidence) + (strat_wt * best_strategy_setup.confidence),
                2
            )

            # Calculate ATR-based position size
            sizing = position_sizer.calculate_position_size(
                symbol=symbol,
                current_price=current_price,
                atr_14=atr,
                portfolio_nav=portfolio_state.nav,
                available_cash=portfolio_state.cash,
                confidence=combined_conf,
            )
            suggested_shares = sizing["shares"]

            # Evaluate transaction cost feasibility
            cost_res = transaction_cost_analyzer.evaluate_cost(
                symbol=symbol,
                price=current_price,
                shares=suggested_shares,
                expected_return_pct=0.045,
                bid_ask_spread_bps=feature_snapshot.liquidity.bid_ask_spread_bps or 4.0,
            )

            if cost_res.status == "REJECT":
                action = ActionType.HOLD
                suggested_shares = 0
                target_weight = 0.0
                reasoning = f"Setup rejected due to transaction cost friction: {cost_res.reason}"
            elif suggested_shares <= 0:
                action = ActionType.HOLD
                target_weight = 0.0
                reasoning = "Sizing engine returned 0 shares due to cash reserve floor or risk limits."
            else:
                action = ActionType.BUY
                target_weight = round(sizing["notional_usd"] / max(1.0, portfolio_state.nav), 4)
                strat_name = best_strategy_setup.strategy.value if hasattr(best_strategy_setup.strategy, "value") else str(best_strategy_setup.strategy)
                reasoning = (
                    f"### High-Conviction Athena V2 Buy Setup for {symbol}\n"
                    f"- **Research Consensus**: {debate_report.consensus_confidence:.0%} confidence ({debate_report.bull_count} BUY / {debate_report.agreement_score:.0%} agreement).\n"
                    f"- **Triggering Strategy**: {strat_name} (Confidence: {best_strategy_setup.confidence:.0%}, R:R: {best_strategy_setup.risk_reward:.1f}:1).\n"
                    f"- **Combined Confidence**: {combined_conf:.0%}.\n"
                    f"- **Market Regime**: {regime_state.regime.value} ({regime_state.description}).\n"
                    f"- **Execution Target**: Buy {suggested_shares} shares @ ~${current_price:.2f} (Target: ${take_profit:.2f}, Stop: ${stop_loss:.2f})."
                )
        else:
            action = ActionType.HOLD
            target_weight = 0.0
            suggested_shares = 0
            combined_conf = debate_report.consensus_confidence
            missing_reasons = []
            if not has_consensus:
                missing_reasons.append(f"Consensus below threshold ({debate_report.consensus_confidence:.0%} < {min_res_conf:.0%})")
            if not has_strategy_setup:
                missing_reasons.append("No active strategy setup qualified")
            if not is_valid:
                missing_reasons.extend(val_reasons)

            reasoning = (
                f"### Hold Stance for {symbol}\n"
                f"- Conditions not satisfied: {'; '.join(missing_reasons)}.\n"
                f"- Preserving capital for qualified high-probability setups."
            )

        return self._create_decision(
            decision_id=decision_id,
            symbol=symbol,
            action=action,
            confidence=combined_conf,
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
                name="Macro Volatility Surge",
                trigger_condition="VIX increases > 20% in session",
                probability=0.15,
                mitigation_action=f"Tighten stop loss to ${round(current_price * 0.985, 2)}",
            ),
            AlternativeScenario(
                name="Sector Multiple Contraction",
                trigger_condition="Benchmark ETF breaks below 20-day moving average",
                probability=0.12,
                mitigation_action="Enforce trailing stop activation",
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
            expected_return_pct=0.045 if action == ActionType.BUY else 0.0,
            expected_drawdown_pct=0.018,
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
