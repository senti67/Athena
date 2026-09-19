"""
ATHENA V2 Agent Orchestrator
Coordinates concurrent execution of the 6 Core Directional Research Agents:
1. TechnicalAgent
2. QuantAgent
3. FundamentalAgent
4. SentimentNewsAgent
5. MacroAgent
6. MicrostructureAgent
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
    TechnicalAgent,
    QuantAgent,
    FundamentalAgent,
    SentimentNewsAgent,
    MacroAgent,
    MicrostructureAgent,
)
from .base import BaseAgent

logger = get_logger("athena.agent_orchestrator")


class AgentOrchestrator:
    """Manages the lifecycle and parallel execution of the 6 ATHENA V2 Research Agents."""

    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.TECHNICAL: TechnicalAgent(),
            AgentType.QUANT: QuantAgent(),
            AgentType.FUNDAMENTAL: FundamentalAgent(),
            AgentType.SENTIMENT_NEWS: SentimentNewsAgent(),
            AgentType.MACRO: MacroAgent(),
            AgentType.MICROSTRUCTURE: MicrostructureAgent(),
        }

    async def run_all_agents(self, context: AgentContext) -> AgentRunSummary:
        """Executes all 6 research agents concurrently and returns aggregated report."""
        tasks = [agent.run(context) for agent in self.agents.values()]
        results: List[AgentOutput] = await asyncio.gather(*tasks)

        outputs_map: Dict[str, AgentOutput] = {}
        supporting: List[str] = []
        opposing: List[str] = []
        neutral: List[str] = []
        unavailable: List[str] = []
        total_conf = 0.0
        active_count = 0

        for out in results:
            outputs_map[out.agent.value] = out
            if out.signal == AgentSignalType.BUY:
                supporting.append(out.agent.value)
                total_conf += out.confidence
                active_count += 1
            elif out.signal == AgentSignalType.SELL:
                opposing.append(out.agent.value)
                total_conf += out.confidence
                active_count += 1
            elif out.signal == AgentSignalType.HOLD:
                neutral.append(out.agent.value)
                total_conf += out.confidence
                active_count += 1
            else:
                unavailable.append(out.agent.value)

        # Aggregate confidence calculated only over available, active agents
        agg_conf = round(total_conf / active_count, 2) if active_count > 0 else 0.0
        diversity_score = round(active_count / len(self.agents), 2)

        qualitative = (
            f"Research Consensus on {context.symbol}: {len(supporting)} BUY, {len(opposing)} SELL, "
            f"{len(neutral)} HOLD, {len(unavailable)} UNAVAILABLE. "
            f"Aggregate Confidence: {agg_conf:.0%}. Domain Availability: {diversity_score:.0%}."
        )

        summary = AgentRunSummary(
            symbol=context.symbol,
            timestamp=datetime.utcnow(),
            agent_outputs=outputs_map,
            supporting_agents=supporting,
            opposing_agents=opposing,
            neutral_agents=neutral,
            unavailable_agents=unavailable,
            aggregate_confidence=agg_conf,
            domain_diversity_score=diversity_score,
            qualitative_summary=qualitative,
        )

        await event_bus.publish(
            Event(
                event_type=EventType.AGENT_ANALYSIS_COMPLETED,
                payload={
                    "symbol": context.symbol,
                    "supporting_count": len(supporting),
                    "opposing_count": len(opposing),
                    "unavailable_count": len(unavailable),
                    "aggregate_confidence": agg_conf,
                    "domain_diversity_score": diversity_score,
                },
            )
        )

        return summary


agent_orchestrator = AgentOrchestrator()
