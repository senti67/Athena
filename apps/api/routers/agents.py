"""
ATHENA Multi-Agent AI Framework Router
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException
from packages.schemas.agent import AgentContext, AgentOutput, AgentRunSummary, AgentType
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.pipeline import data_pipeline
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector

router = APIRouter(prefix="/agents", tags=["AI Agents"])


@router.get("")
async def list_agents():
    """Lists all registered analytical and operational AI agents."""
    return [
        {
            "id": agent_type.value,
            "name": agent_type.value.replace("_", " ").title() + " Agent",
            "version": agent.version,
            "type": agent_type.value,
            "description": f"Autonomous {agent_type.value} intelligence module",
        }
        for agent_type, agent in agent_orchestrator.agents.items()
    ]


@router.get("/{agent_name}")
async def get_agent_detail(agent_name: str):
    try:
        at = AgentType(agent_name.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    agent = agent_orchestrator.agents[at]
    return {
        "id": at.value,
        "name": at.value.replace("_", " ").title() + " Agent",
        "version": agent.version,
        "model": agent.model_name,
    }


@router.post("/{agent_name}/analyze", response_model=AgentOutput)
async def analyze_single_agent(agent_name: str, symbol: str = "AAPL"):
    try:
        at = AgentType(agent_name.lower())
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    sym = symbol.upper()
    candles = await data_pipeline.ingest_candles(sym, limit=150)
    features = feature_pipeline.compute_features(sym, candles)
    regime = regime_detector.detect_regime(features)

    context = AgentContext(
        symbol=sym,
        feature_snapshot=features,
        regime_state=regime,
    )
    return await agent_orchestrator.agents[at].run(context)


@router.post("/run-all", response_model=AgentRunSummary)
async def run_all_agents(symbol: str = "AAPL"):
    sym = symbol.upper()
    candles = await data_pipeline.ingest_candles(sym, limit=150)
    features = feature_pipeline.compute_features(sym, candles)
    regime = regime_detector.detect_regime(features)

    context = AgentContext(
        symbol=sym,
        feature_snapshot=features,
        regime_state=regime,
    )
    return await agent_orchestrator.run_all_agents(context)
