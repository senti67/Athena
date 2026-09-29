"""
ATHENA Quantitative Module Orchestrator
Coordinates concurrent execution of the orthogonal analytical research modules:
1. TechnicalTrendModule
2. MomentumModule
3. MeanReversionModule
4. VolatilityRiskModule
5. FundamentalModule
6. SentimentNewsModule
7. MarketRegimeModule
8. CrossAssetMacroModule
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
    CrossAssetMacroModule,
    FundamentalModule,
    MarketRegimeModule,
    MeanReversionModule,
    MicrostructureModule,
    MomentumModule,
    SentimentNewsModule,
    TechnicalTrendModule,
    VolatilityRiskModule,
)
from .base import BaseAgent

logger = get_logger("athena.agent_orchestrator")


class AgentOrchestrator:
    """Manages the lifecycle and parallel execution of ATHENA Analytical Modules."""

    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.TECHNICAL_TREND: TechnicalTrendModule(),
            AgentType.MOMENTUM: MomentumModule(),
            AgentType.MEAN_REVERSION: MeanReversionModule(),
            AgentType.VOLATILITY_RISK: VolatilityRiskModule(),
            AgentType.FUNDAMENTAL: FundamentalModule(),
            AgentType.SENTIMENT_NEWS: SentimentNewsModule(),
            AgentType.MARKET_REGIME: MarketRegimeModule(),
            AgentType.CROSS_ASSET_MACRO: CrossAssetMacroModule(),
        }

    async def run_all_agents(self, context: AgentContext) -> AgentRunSummary:
        """Executes analytical modules concurrently and returns aggregated report."""
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
            agent_key = out.agent.value if hasattr(out.agent, "value") else str(out.agent)
            outputs_map[agent_key] = out
            if out.signal == AgentSignalType.BUY:
                supporting.append(agent_key)
                total_conf += out.confidence
                active_count += 1
            elif out.signal == AgentSignalType.SELL:
                opposing.append(agent_key)
                total_conf += out.confidence
                active_count += 1
            elif out.signal == AgentSignalType.HOLD:
                neutral.append(agent_key)
                total_conf += out.confidence
                active_count += 1
            else:
                unavailable.append(agent_key)

        agg_conf = round(total_conf / active_count, 2) if active_count > 0 else 0.0
        diversity_score = round(active_count / len(self.agents), 2)

        qualitative = (
            f"Module Analysis on {context.symbol}: {len(supporting)} BUY, {len(opposing)} SELL, "
            f"{len(neutral)} HOLD, {len(unavailable)} UNAVAILABLE. "
            f"Aggregate Confidence: {agg_conf:.0%}. Available Domains: {diversity_score:.0%}."
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
