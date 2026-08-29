"""
ATHENA Trade Journal & Explainability Engine
Generates institutional Markdown Trade Explainability Reports and persists full lineage.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from packages.logging.logger import get_logger
from packages.schemas.decision import TradingDecision
from packages.schemas.journal import ExplainabilityReport, TradeJournalEntry
from packages.schemas.order import Fill, OrderResponse
from packages.schemas.risk import RiskCheckResult
from services.memory_service.memory import memory_service

logger = get_logger("athena.trade_journal")


class TradeJournalService:
    """Maintains trade records and auto-generates comprehensive explainability reports."""

    def __init__(self):
        self.journal: Dict[str, TradeJournalEntry] = {}

    def record_entry(
        self,
        decision: TradingDecision,
        risk_check: RiskCheckResult,
        order_response: OrderResponse,
    ) -> TradeJournalEntry:
        trade_id = f"TRD-{decision.symbol}-{uuid.uuid4().hex[:6].upper()}"
        fills = order_response.fills
        entry_price = order_response.average_fill_price or decision.current_price
        shares = sum(f.quantity for f in fills) if fills else float(risk_check.max_approved_shares)
        total_cost = entry_price * shares

        # Generate Explainability Report
        report = self._build_explainability_report(trade_id, decision, risk_check, entry_price, shares)

        entry = TradeJournalEntry(
            trade_id=trade_id,
            symbol=decision.symbol,
            action=decision.action.value,
            entry_time=datetime.utcnow(),
            entry_price=entry_price,
            shares=shares,
            total_cost=total_cost,
            status="OPEN",
            regime_at_entry=decision.regime,
            decision_snapshot=decision,
            risk_check_snapshot=risk_check,
            order_fills=fills,
            confidence_at_entry=decision.confidence,
            predicted_return=decision.expected_return_pct,
            explainability_report_markdown=report.rendered_markdown,
            tags=[decision.symbol, decision.regime, decision.action.value],
        )

        self.journal[trade_id] = entry
        memory_service.record_trade(entry)
        logger.info(f"Created trade journal entry {trade_id} with full explainability trace.")
        return entry

    def close_trade(self, trade_id: str, exit_price: float, exit_time: Optional[datetime] = None) -> TradeJournalEntry:
        """Closes a trade, computes realized PnL, and updates learning records."""
        if trade_id not in self.journal:
            raise KeyError(f"Trade ID {trade_id} not found in journal.")

        entry = self.journal[trade_id]
        entry.exit_price = exit_price
        entry.exit_time = exit_time or datetime.utcnow()
        entry.status = "CLOSED"

        if entry.action == "BUY":
            pnl = (exit_price - entry.entry_price) * entry.shares
            pnl_pct = (exit_price - entry.entry_price) / entry.entry_price
        else:
            pnl = (entry.entry_price - exit_price) * entry.shares
            pnl_pct = (entry.entry_price - exit_price) / entry.entry_price

        entry.realized_pnl = round(pnl, 2)
        entry.realized_pnl_pct = round(pnl_pct, 4)
        entry.actual_return = pnl_pct
        entry.prediction_error = round(abs(entry.predicted_return - pnl_pct), 4)

        logger.info(f"Closed trade {trade_id}: PnL=${pnl:,.2f} ({pnl_pct*100:+.2f}%)")
        return entry

    def _build_explainability_report(
        self,
        trade_id: str,
        decision: TradingDecision,
        risk_check: RiskCheckResult,
        entry_price: float,
        shares: float,
    ) -> ExplainabilityReport:
        scenarios_text = "\n".join(
            [f"- **{s.name}** (Prob: {s.probability*100:.0f}%): {s.mitigation_action}" for s in decision.alternative_scenarios]
        )

        md = f"""# ATHENA INSTITUTIONAL TRADE REPORT

**Trade ID**: `{trade_id}`  
**Symbol**: `{decision.symbol}`  
**Decision**: `{decision.action.value}`  
**Confidence**: `{decision.confidence*100:.1f}%` (Calibrated Prob: `{decision.calibrated_probability*100:.1f}%`)  
**Regime**: `{decision.regime}`  
**Timestamp**: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}`  

---

### Supporting Agents ({len(decision.supporting_agents)})
{', '.join(decision.supporting_agents) if decision.supporting_agents else 'None'}

### Opposing Agents ({len(decision.opposing_agents)})
{', '.join(decision.opposing_agents) if decision.opposing_agents else 'None'}

---

### Trade Parameters & Execution Bounds
* **Entry Fill Price**: `${entry_price:,.2f}`
* **Position Size**: `{shares:,.0f} shares` (`${entry_price * shares:,.2f}`)
* **Stop Loss**: `${decision.stop_loss:,.2f}` (`-{(entry_price - decision.stop_loss)/entry_price*100:.2f}%`)
* **Take Profit**: `${decision.take_profit:,.2f}` (`+{(decision.take_profit - entry_price)/entry_price*100:.2f}%`)
* **Expected Return**: `+{decision.expected_return_pct*100:.2f}%`
* **Expected Drawdown**: `-{decision.expected_drawdown_pct*100:.2f}%`
* **Reward-to-Risk Ratio**: `{decision.risk_reward_ratio}:1`

---

### Alternative Scenarios & Hedging
{scenarios_text}

---

### Why the Trade Was Approved
1. **Multi-Agent Consensus**: Dialectical debate achieved an agreement score of `{decision.debate_agreement_score:.2f}`.
2. **Empirical Validation**: Statistical significance verified with positive risk-reward margin net of transaction costs.
3. **Independent Risk Veto**: Cleared all exposure, concentration, leverage, and drawdown checks with a safe risk score of `{risk_check.risk_score:.2f}`.
"""
        return ExplainabilityReport(
            trade_id=trade_id,
            symbol=decision.symbol,
            timestamp=datetime.utcnow(),
            decision=decision.action.value,
            confidence_pct=round(decision.confidence * 100.0, 1),
            regime=decision.regime,
            supporting_agents=decision.supporting_agents,
            opposing_agents=decision.opposing_agents,
            strongest_evidence=[],
            weakest_evidence=[],
            risk_assessment=f"Risk Score: {risk_check.risk_score:.2f}. Cleared all exposure rules.",
            position_sizing_rationale=f"Target weight {decision.target_weight*100:.1f}% NAV.",
            stop_loss_rationale=f"Stop loss placed at ${decision.stop_loss:.2f}.",
            take_profit_rationale=f"Take profit target at ${decision.take_profit:.2f}.",
            expected_return_pct=decision.expected_return_pct * 100.0,
            expected_drawdown_pct=decision.expected_drawdown_pct * 100.0,
            alternative_scenarios=[s.name for s in decision.alternative_scenarios],
            why_trade_approved="Passed multi-agent debate consensus and independent risk veto checks.",
            rendered_markdown=md,
        )


journal_service = TradeJournalService()
