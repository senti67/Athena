"""
ATHENA Dialectical Debate Router
"""

from fastapi import APIRouter
from packages.schemas.agent import AgentContext
from packages.schemas.debate import DebateReport
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.pipeline import data_pipeline
from services.debate_service.engine import debate_engine
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector
from services.strategy_service.registry import strategy_registry

router = APIRouter(prefix="/debates", tags=["Debate Engine"])


@router.post("/generate", response_model=DebateReport)
async def generate_debate(symbol: str = "AAPL"):
    sym = symbol.upper()
    candles = await data_pipeline.ingest_candles(sym, limit=150)
    features = feature_pipeline.compute_features(sym, candles)
    regime = regime_detector.detect_regime(features)

    context = AgentContext(
        symbol=sym,
        feature_snapshot=features,
        regime_state=regime,
    )

    agent_summary = await agent_orchestrator.run_all_agents(context)
    strat_outputs = strategy_registry.run_all_strategies(context)

    return debate_engine.conduct_debate(sym, agent_summary, strat_outputs)
