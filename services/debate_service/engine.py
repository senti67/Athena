"""
ATHENA Dialectical Debate Engine
Synthesizes reports from all 14 agents and 16 strategies, analyzes consensus/conflicts,
and produces dialectical synthesis without overriding risk controls.
"""

from datetime import datetime
from typing import Dict, List
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentRunSummary, AgentSignalType
from packages.schemas.debate import ConflictItem, DebateReport
from packages.schemas.events import Event, EventType
from packages.schemas.strategy import StrategyOutput, StrategySignal

logger = get_logger("athena.debate_engine")


class DebateEngine:
    """Coordinates dialectical synthesis across analytical agents and quantitative strategies."""

    def conduct_debate(
        self,
        symbol: str,
        agent_summary: AgentRunSummary,
        strategy_outputs: Dict[str, StrategyOutput],
    ) -> DebateReport:
        bull_agents = agent_summary.supporting_agents
        bear_agents = agent_summary.opposing_agents
        neutral_agents = agent_summary.neutral_agents

        total_agents = len(agent_summary.agent_outputs)
        bull_count = len(bull_agents)
        bear_count = len(bear_agents)
        neutral_count = len(neutral_agents)

        # 1. Consensus Agreement Score
        max_side = max(bull_count, bear_count)
        agreement_score = round(max_side / total_agents, 2) if total_agents > 0 else 0.50

        # 2. Extract Evidence & Blind spots
        strongest_bullish: List[str] = []
        strongest_bearish: List[str] = []
        weakest_evidence: List[str] = []
        missing_info: List[str] = []

        for name, out in agent_summary.agent_outputs.items():
            if out.signal == AgentSignalType.BUY:
                strongest_bullish.extend([f"[{name.upper()}] {p}" for p in out.bullish_points[:2]])
            elif out.signal == AgentSignalType.SELL:
                strongest_bearish.extend([f"[{name.upper()}] {p}" for p in out.bearish_points[:2]])

            if out.confidence < 0.65:
                weakest_evidence.append(f"Low confidence ({out.confidence:.2f}) from {name}")

        if not strongest_bearish:
            missing_info.append("Counter-thesis evidence is light; watch for macro or earnings surprises.")

        # 3. Identify Direct Conflicts (e.g. Valuation vs Momentum, Technical vs Macro)
        conflicts: List[ConflictItem] = []
        if "fundamental" in agent_summary.agent_outputs and "technical" in agent_summary.agent_outputs:
            fund_out = agent_summary.agent_outputs["fundamental"]
            tech_out = agent_summary.agent_outputs["technical"]
            if fund_out.signal != tech_out.signal:
                conflicts.append(
                    ConflictItem(
                        agents_involved=["fundamental", "technical"],
                        topic="Valuation multiple vs Price momentum",
                        agent_a_position=f"Fundamental: {fund_out.signal.value}",
                        agent_b_position=f"Technical: {tech_out.signal.value}",
                        severity=0.65,
                        resolution="Favor short-term momentum for entry timing while observing valuation ceiling.",
                    )
                )

        if "macro" in agent_summary.agent_outputs and "technical" in agent_summary.agent_outputs:
            macro_out = agent_summary.agent_outputs["macro"]
            tech_out = agent_summary.agent_outputs["technical"]
            if macro_out.signal == AgentSignalType.HOLD and tech_out.signal == AgentSignalType.BUY:
                conflicts.append(
                    ConflictItem(
                        agents_involved=["macro", "technical"],
                        topic="Macro caution vs Technical breakout",
                        agent_a_position="Macro advises caution due to interest rate cycle",
                        agent_b_position="Technical detects strong breakout above resistance",
                        severity=0.50,
                        resolution="Proceed with trade but implement tighter stop loss to protect against macro volatility.",
                    )
                )

        # 4. Synthesize Dialectical Conclusion
        if bull_count > bear_count:
            recommended_action = "BUY"
            consensus_conf = round(agent_summary.aggregate_confidence, 2)
            debate_synthesis = (
                f"Multi-agent dialectical consensus supports a {recommended_action} recommendation. "
                f"{bull_count}/{total_agents} agents support the thesis, backed by {len(strategy_outputs)} quantitative models. "
                f"Core drivers: {strongest_bullish[0] if strongest_bullish else 'Momentum and factor alignment'}."
            )
        elif bear_count > bull_count:
            recommended_action = "SELL"
            consensus_conf = round(agent_summary.aggregate_confidence, 2)
            debate_synthesis = (
                f"Multi-agent debate favors a {recommended_action} / defensive stance. "
                f"{bear_count}/{total_agents} agents present valid headwind evidence."
            )
        else:
            recommended_action = "HOLD"
            consensus_conf = 0.50
            debate_synthesis = "Dialectical deadlock between bullish momentum and bearish valuation. Recommending HOLD."

        report = DebateReport(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            agreement_score=agreement_score,
            conflicts=conflicts,
            strongest_bullish_evidence=strongest_bullish[:5],
            strongest_bearish_evidence=strongest_bearish[:5],
            weakest_evidence=weakest_evidence[:3],
            missing_information=missing_info,
            bull_count=bull_count,
            bear_count=bear_count,
            neutral_count=neutral_count,
            debate_synthesis=debate_synthesis,
            recommended_action=recommended_action,
            consensus_confidence=consensus_conf,
        )

        return report


debate_engine = DebateEngine()
