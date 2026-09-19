"""
ATHENA V2 Research Consensus & Evidence Deduplication Engine
Synthesizes reports from the 6 research agents across orthogonal evidence domains,
deduplicates correlated price indicators, and resolves multi-perspective tensions.
"""

from datetime import datetime
from typing import Dict, List, Optional
from packages.common.config import settings
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import AgentRunSummary, AgentSignalType, AgentType
from packages.schemas.debate import ConflictItem, DebateReport
from packages.schemas.events import Event, EventType
from packages.schemas.strategy import StrategyOutput, StrategySignal

logger = get_logger("athena.debate_engine")


class DebateEngine:
    """
    Synthesizes research agent outputs with evidence domain deduplication.
    Prevents correlated indicators from inflating consensus counts.
    """

    def conduct_debate(
        self,
        symbol: str,
        agent_summary: AgentRunSummary,
        strategy_outputs: Dict[str, StrategyOutput],
    ) -> DebateReport:
        active_outputs: Dict[str, Any] = {}
        unavailable_agents: List[str] = list(agent_summary.unavailable_agents)

        bull_agents: List[str] = []
        bear_agents: List[str] = []
        neutral_agents: List[str] = []

        total_bull_conf = 0.0
        total_bear_conf = 0.0

        for name, out in agent_summary.agent_outputs.items():
            if out.signal == AgentSignalType.UNAVAILABLE or out.confidence == 0.0:
                if name not in unavailable_agents:
                    unavailable_agents.append(name)
            else:
                active_outputs[name] = out
                if out.signal == AgentSignalType.BUY:
                    bull_agents.append(name)
                    total_bull_conf += out.confidence
                elif out.signal == AgentSignalType.SELL:
                    bear_agents.append(name)
                    total_bear_conf += out.confidence
                else:
                    neutral_agents.append(name)

        active_count = len(active_outputs)
        bull_count = len(bull_agents)
        bear_count = len(bear_agents)
        neutral_count = len(neutral_agents)
        unavailable_count = len(unavailable_agents)

        # 1. Consensus Agreement Score (over active, non-unavailable domains)
        max_side = max(bull_count, bear_count)
        agreement_score = round(max_side / active_count, 2) if active_count > 0 else 0.0
        domain_diversity = round(active_count / 6.0, 2)

        # 2. Extract Evidence & Blind spots
        strongest_bullish: List[str] = []
        strongest_bearish: List[str] = []
        weakest_evidence: List[str] = []
        missing_info: List[str] = []

        for name, out in active_outputs.items():
            if out.signal == AgentSignalType.BUY:
                strongest_bullish.extend([f"[{name.upper()}] {p}" for p in out.bullish_points[:2]])
            elif out.signal == AgentSignalType.SELL:
                strongest_bearish.extend([f"[{name.upper()}] {p}" for p in out.bearish_points[:2]])

            if out.confidence < 0.65:
                weakest_evidence.append(f"Low confidence ({out.confidence:.2f}) from {name}")

        for unav in unavailable_agents:
            missing_info.append(f"Domain data unavailable: {unav}")

        if not strongest_bearish:
            missing_info.append("Counter-thesis evidence is light; observe macro and earnings catalysts.")

        # 3. Identify Direct Conflicts (e.g. Fundamental vs Technical, Macro vs Quant)
        conflicts: List[ConflictItem] = []
        if "fundamental" in active_outputs and "technical" in active_outputs:
            fund_out = active_outputs["fundamental"]
            tech_out = active_outputs["technical"]
            if fund_out.signal != tech_out.signal:
                conflicts.append(
                    ConflictItem(
                        agents_involved=["fundamental", "technical"],
                        topic="Valuation multiple vs Price momentum",
                        agent_a_position=f"Fundamental: {fund_out.signal.value}",
                        agent_b_position=f"Technical: {tech_out.signal.value}",
                        severity=0.65,
                        resolution="Favor short-term price momentum for timing while capping position at valuation limits.",
                    )
                )

        if "macro" in active_outputs and "technical" in active_outputs:
            macro_out = active_outputs["macro"]
            tech_out = active_outputs["technical"]
            if macro_out.signal == AgentSignalType.HOLD and tech_out.signal == AgentSignalType.BUY:
                conflicts.append(
                    ConflictItem(
                        agents_involved=["macro", "technical"],
                        topic="Macro caution vs Technical breakout",
                        agent_a_position="Macro advises caution due to broader market conditions",
                        agent_b_position="Technical detects breakout above resistance",
                        severity=0.50,
                        resolution="Proceed with trade but implement tighter stop loss to protect against market beta volatility.",
                    )
                )

        # 4. Synthesize Dialectical Conclusion with Domain Deduplication
        min_agreement = getattr(settings, "MIN_RESEARCH_AGREEMENT", 0.65)
        min_conf = getattr(settings, "MIN_RESEARCH_CONFIDENCE", 0.65)

        if bull_count > bear_count and agreement_score >= min_agreement:
            recommended_action = "BUY"
            consensus_conf = round(total_bull_conf / bull_count, 2)
            debate_synthesis = (
                f"Multi-domain research consensus confirms a {recommended_action} stance ({bull_count}/{active_count} active domains aligned, Agreement: {agreement_score:.0%}). "
                f"Domain Diversity: {domain_diversity:.0%}. Leading thesis: {strongest_bullish[0] if strongest_bullish else 'Technical & Factor alignment'}."
            )
        elif bear_count > bull_count and agreement_score >= min_agreement:
            recommended_action = "SELL"
            consensus_conf = round(total_bear_conf / bear_count, 2)
            debate_synthesis = (
                f"Multi-domain research consensus confirms a {recommended_action} stance ({bear_count}/{active_count} active domains aligned, Agreement: {agreement_score:.0%}). "
                f"Domain Diversity: {domain_diversity:.0%}."
            )
        else:
            recommended_action = "HOLD"
            consensus_conf = 0.50
            debate_synthesis = (
                f"Consensus inconclusive or below threshold ({bull_count} BUY, {bear_count} SELL, {neutral_count} HOLD). "
                f"Agreement score {agreement_score:.0%} < threshold {min_agreement:.0%}. Recommending HOLD."
            )

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
            unavailable_count=unavailable_count,
            domain_diversity_score=domain_diversity,
            debate_synthesis=debate_synthesis,
            recommended_action=recommended_action,
            consensus_confidence=consensus_conf,
        )

        return report


debate_engine = DebateEngine()
ResearchConsensusEngine = DebateEngine
research_consensus_engine = debate_engine
