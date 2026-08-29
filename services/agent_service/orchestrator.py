"""
ATHENA Agent Orchestrator
Coordinates concurrent execution of all 14 specialized AI agents.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.agent import (
    AgentContext,
    AgentOutput,
    AgentRunSummary,
    AgentSignalType,
    AgentType,
)
from packages.schemas.events import Event, EventType
from .agents import (
    ComplianceAgent,
    CostAnalysisAgent,
    CrossAssetAgent,
    DataQualityAgentWrapper,
    FundamentalAgent,
    MacroAgent,
    MicrostructureAgent,
    OptionsAgent,
    PatternDiscoveryAgent,
    QuantAgent,
    ResearchAgent,
    SentimentAgent,
    SimulationAgent,
    TechnicalAgent,
)
from .base import BaseAgent

logger = get_logger("athena.agent_orchestrator")


class AgentOrchestrator:
    """Manages the lifecycle and parallel execution of the 14 AI agents."""

    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.TECHNICAL: TechnicalAgent(),
            AgentType.QUANT: QuantAgent(),
            AgentType.FUNDAMENTAL: FundamentalAgent(),
            AgentType.SENTIMENT: SentimentAgent(),
            AgentType.MACRO: MacroAgent(),
            AgentType.MICROSTRUCTURE: MicrostructureAgent(),
            AgentType.OPTIONS: OptionsAgent(),
            AgentType.CROSS_ASSET: CrossAssetAgent(),
            AgentType.PATTERN_DISCOVERY: PatternDiscoveryAgent(),
            AgentType.SIMULATION: SimulationAgent(),
            AgentType.DATA_QUALITY: DataQualityAgentWrapper(),
            AgentType.COMPLIANCE: ComplianceAgent(),
            AgentType.COST_ANALYSIS: CostAnalysisAgent(),
            AgentType.RESEARCH: ResearchAgent(),
        }

    async def run_all_agents(self, context: AgentContext) -> AgentRunSummary:
        """Executes all 14 agents concurrently and returns aggregated report."""
        tasks = [agent.run(context) for agent in self.agents.values()]
        results: List[AgentOutput] = await asyncio.gather(*tasks)

        outputs_map: Dict[str, AgentOutput] = {}
        supporting: List[str] = []
        opposing: List[str] = []
        neutral: List[str] = []
        total_conf = 0.0

        for out in results:
            outputs_map[out.agent.value] = out
            if out.signal == AgentSignalType.BUY:
                supporting.append(out.agent.value)
            elif out.signal == AgentSignalType.SELL:
                opposing.append(out.agent.value)
            else:
                neutral.append(out.agent.value)
            total_conf += out.confidence

        agg_conf = round(total_conf / len(results), 2) if results else 0.0

        summary = AgentRunSummary(
            symbol=context.symbol,
            timestamp=datetime.utcnow(),
            agent_outputs=outputs_map,
            supporting_agents=supporting,
            opposing_agents=opposing,
            neutral_agents=neutral,
            aggregate_confidence=agg_conf,
        )

        await event_bus.publish(
            Event(
                event_type=EventType.AGENT_ANALYSIS_COMPLETED,
                payload={
                    "symbol": context.symbol,
                    "supporting_count": len(supporting),
                    "opposing_count": len(opposing),
                    "aggregate_confidence": agg_conf,
                },
            )
        )

        return summary


agent_orchestrator = AgentOrchestrator()
