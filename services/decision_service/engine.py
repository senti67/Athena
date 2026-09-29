"""
ATHENA Quantitative Decision Engine
Synthesizes Correlation-Aware Signal Aggregation, Active Strategy Setups, Expected Edge Estimation,
Dynamic ATR-Based Exits, Compliance, and Volatility-Aware Sizing into fully explainable TradingDecisions.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from packages.common.config import settings
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.quant.metrics import calculate_expected_edge
from packages.schemas.agent import AgentRunSummary
from packages.schemas.debate import DebateReport
from packages.schemas.decision import ActionType, AlternativeScenario, TradingDecision
from packages.schemas.events import Event, EventType
from packages.schemas.feature import FeatureSnapshot
from packages.schemas.portfolio import PortfolioState
from packages.schemas.regime import RegimeState
from packages.schemas.strategy import StrategyOutput, StrategySignal
from services.risk_service.compliance import compliance_engine
from services.risk_service.cost_analyzer import transaction_cost_analyzer
from services.risk_service.position_sizer import position_sizer
from services.validator_service.validator import evidence_validator

logger = get_logger("athena.decision_engine")


class DecisionEngine:
    """
    Synthesizes research consensus, strategy setups, and risk guardrails into execution-ready decisions.
    Strictly enforces expected edge, risk-to-reward ratio, and data quality requirements.
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

        # 1. ATR and Dynamic Volatility-Aware Stop Loss / Take Profit Levels
        stop_mult = getattr(settings, "ATHENA_ATR_STOP_MULTIPLIER", 2.0)
        target_mult = getattr(settings, "ATHENA_ATR_TARGET_MULTIPLIER", 3.5)
        atr = feature_snapshot.technical.atr_14 or (current_price * 0.015)

        stop_loss = round(max(current_price * 0.90, current_price - (stop_mult * atr)), 2)
        take_profit = round(current_price + (target_mult * atr), 2)
        risk_distance = max(0.01, current_price - stop_loss)
        reward_distance = max(0.01, take_profit - current_price)
        risk_reward = round(reward_distance / risk_distance, 2)

        stop_loss_pct = round(risk_distance / current_price, 4) if current_price > 0 else 0.025
        take_profit_pct = round(reward_distance / current_price, 4) if current_price > 0 else 0.060

        # 2. Existing Active Position Management (Exit & Profit Taking Rules)
        if existing_position and existing_position.shares > 0:
            entry_px = existing_position.average_entry_price
            pnl_pct = (current_price - entry_px) / entry_px if entry_px > 0 else 0.0

            # Profit Target Reached (+3.0% or above take_profit level)
            if current_price >= take_profit or pnl_pct >= 0.030:
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
                    expected_edge=pnl_pct,
                    expected_value=pnl_pct,
                    reasoning=f"Take Profit Target Reached (+{pnl_pct*100:.2f}% gain). Realizing gains and recycling capital.",
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
                    expected_edge=pnl_pct,
                    expected_value=pnl_pct,
                    reasoning=f"Stop Loss Level Breached ({pnl_pct*100:.2f}% loss). Cutting loss to protect portfolio capital.",
                    agent_summary=agent_summary,
                    debate_report=debate_report,
                    regime_state=regime_state,
                    is_valid=True,
                    val_reasons=["Stop loss boundary reached."],
                )

            # Active position holding (prevent duplicate buying)
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
                expected_edge=pnl_pct,
                expected_value=pnl_pct,
                reasoning=f"Active Position Held: Current P&L is {pnl_pct*100:+.2f}%. Holding for profit target ${take_profit:.2f}.",
                agent_summary=agent_summary,
                debate_report=debate_report,
                regime_state=regime_state,
                is_valid=True,
                val_reasons=["Asset already held; awaiting target expansion."],
            )

        # 3. New Entry Qualification & Expected Edge Estimation
        if best_strategy_setup is None:
            valid_setups = [
                s for s in strategy_outputs.values()
                if s.signal == StrategySignal.BUY and s.is_active
            ]
            if valid_setups:
                valid_setups.sort(key=lambda s: (s.expected_edge, s.confidence, s.risk_reward), reverse=True)
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

        # Configurable Institutional Thresholds
        min_signal = getattr(settings, "ATHENA_MIN_SIGNAL_SCORE", 0.55)
        min_edge = getattr(settings, "ATHENA_MIN_EXPECTED_EDGE", 0.012)
        min_rr = getattr(settings, "ATHENA_MIN_RISK_REWARD", 1.8)
        min_regime = getattr(settings, "ATHENA_MIN_REGIME_SCORE", 0.50)
        min_res_conf = getattr(settings, "MIN_RESEARCH_CONFIDENCE", 0.60)
        min_strat_conf = getattr(settings, "MIN_STRATEGY_CONFIDENCE", 0.60)

        # Estimated Expected Edge
        win_rate = best_strategy_setup.win_rate if best_strategy_setup else 0.55
        expected_edge = calculate_expected_edge(win_rate, take_profit_pct, stop_loss_pct)

        has_aggregator_buy = (
            debate_report.recommended_action == "BUY"
            and debate_report.composite_score >= min_signal
            and debate_report.consensus_confidence >= min_res_conf
        )

        has_strategy_setup = (
            best_strategy_setup is not None
            and best_strategy_setup.signal == StrategySignal.BUY
            and best_strategy_setup.confidence >= min_strat_conf
            and best_strategy_setup.risk_reward >= min_rr
        )

        has_sufficient_edge = (expected_edge >= min_edge)
        has_regime_support = (regime_state.confidence >= min_regime)

        if is_valid and has_aggregator_buy and has_strategy_setup and has_sufficient_edge and has_regime_support:
            agent_wt = getattr(settings, "AGENT_WEIGHT", 0.50)
            strat_wt = getattr(settings, "STRATEGY_WEIGHT", 0.50)
            combined_conf = round(
                (agent_wt * debate_report.consensus_confidence) + (strat_wt * best_strategy_setup.confidence),
                2,
            )

            # Volatility-Aware Position Sizing
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
                expected_return_pct=expected_edge,
                bid_ask_spread_bps=feature_snapshot.liquidity.bid_ask_spread_bps or 3.5,
            )

            if cost_res.status == "REJECT":
                action = ActionType.HOLD
                suggested_shares = 0
                target_weight = 0.0
                reasoning = f"Setup rejected due to transaction cost friction: {cost_res.reason}"
            elif suggested_shares <= 0:
                action = ActionType.HOLD
                target_weight = 0.0
                reasoning = "Sizing engine returned 0 shares due to cash constraints or risk caps."
            else:
                action = ActionType.BUY
                target_weight = round(sizing["notional_usd"] / max(1.0, portfolio_state.nav), 4)
                strat_name = best_strategy_setup.strategy.value if hasattr(best_strategy_setup.strategy, "value") else str(best_strategy_setup.strategy)
                reasoning = (
                    f"### High-Conviction Athena Quantitative Buy Setup for {symbol}\n"
                    f"- **Aggregator Composite Score**: {debate_report.composite_score:+.2f} (Confidence: {debate_report.consensus_confidence:.0%}).\n"
                    f"- **Triggering Strategy**: {strat_name} (Confidence: {best_strategy_setup.confidence:.0%}, R:R: {risk_reward:.1f}:1).\n"
                    f"- **Estimated Expected Edge**: +{expected_edge*100:.2f}% (P_win: {win_rate*100:.0f}%, Target: +{take_profit_pct*100:.1f}%, Stop: -{stop_loss_pct*100:.1f}%).\n"
                    f"- **Market Regime**: {regime_state.regime.value} ({regime_state.description}).\n"
                    f"- **Execution Target**: Buy {suggested_shares} shares @ ~${current_price:.2f} (TP: ${take_profit:.2f}, SL: ${stop_loss:.2f})."
                )
        else:
            action = ActionType.HOLD
            target_weight = 0.0
            suggested_shares = 0
            combined_conf = debate_report.consensus_confidence
            missing_reasons = []

            if not has_aggregator_buy:
                missing_reasons.append(f"Aggregator score {debate_report.composite_score:+.2f} < {min_signal:.2f}")
            if not has_strategy_setup:
                missing_reasons.append("No active strategy qualified")
            if not has_sufficient_edge:
                missing_reasons.append(f"Expected edge {expected_edge*100:+.2f}% < {min_edge*100:.1f}%")
            if not is_valid:
                missing_reasons.extend(val_reasons)

            reasoning = (
                f"### Hold Stance for {symbol}\n"
                f"- Conditions not satisfied: {'; '.join(missing_reasons)}.\n"
                f"- Preserving capital for qualified high-edge setups."
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
            expected_edge=expected_edge,
            expected_value=expected_edge,
            reasoning=reasoning,
            agent_summary=agent_summary,
            debate_report=debate_report,
            regime_state=regime_state,
            is_valid=is_valid,
            val_reasons=val_reasons,
            triggering_strategy=best_strategy_setup.strategy.value if (best_strategy_setup and action == ActionType.BUY) else None,
            strategy_scores={k: v.confidence for k, v in strategy_outputs.items()},
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
        expected_edge: float,
        expected_value: float,
        reasoning: str,
        agent_summary: AgentRunSummary,
        debate_report: DebateReport,
        regime_state: RegimeState,
        is_valid: bool,
        val_reasons: List[str],
        triggering_strategy: Optional[str] = None,
        strategy_scores: Optional[Dict[str, float]] = None,
    ) -> TradingDecision:
        scenarios = [
            AlternativeScenario(
                name="Macro Volatility Expansion",
                trigger_condition="VIX increases > 20% in session",
                probability=0.15,
                mitigation_action=f"Tighten stop loss to ${round(current_price * 0.985, 2)}",
            ),
            AlternativeScenario(
                name="Trend Support Breakdown",
                trigger_condition="Price breaks below 50-day EMA",
                probability=0.12,
                mitigation_action="Enforce trailing stop exit",
            ),
        ]

        model_versions = {
            name: out.model_version for name, out in agent_summary.agent_outputs.items()
        }

        exec_mode = "ANALYSIS_ONLY" if getattr(settings, "ATHENA_ANALYSIS_ONLY", False) or settings.EXECUTION_MODE == "ANALYSIS_ONLY" else "PAPER"

        return TradingDecision(
            id=decision_id,
            timestamp=datetime.utcnow(),
            symbol=symbol,
            action=action,
            confidence=confidence,
            calibrated_probability=round(confidence * 0.90, 2),
            current_price=current_price,
            target_weight=target_weight,
            suggested_shares=suggested_shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
            expected_edge=round(expected_edge, 4),
            expected_value=round(expected_value, 4),
            expected_return_pct=round(abs(take_profit - current_price) / max(1.0, current_price), 4) if action == ActionType.BUY else 0.0,
            expected_drawdown_pct=round(abs(current_price - stop_loss) / max(1.0, current_price), 4),
            risk_reward_ratio=risk_reward,
            holding_period="5D",
            regime=regime_state.regime.value if hasattr(regime_state.regime, "value") else str(regime_state.regime),
            regime_compatibility=debate_report.agreement_score,
            data_quality_score=1.0,
            triggering_strategy=triggering_strategy,
            feature_group_scores=debate_report.feature_group_scores,
            strategy_scores=strategy_scores or {},
            debate_agreement_score=debate_report.agreement_score,
            supporting_agents=agent_summary.supporting_agents,
            opposing_agents=agent_summary.opposing_agents,
            reasoning=reasoning,
            alternative_scenarios=scenarios,
            model_versions=model_versions,
            validation_status="VALIDATED" if is_valid else "REJECTED",
            validation_reasons=val_reasons,
            execution_mode=exec_mode,
        )


decision_engine = DecisionEngine()
