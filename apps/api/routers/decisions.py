"""
ATHENA Decision Engine Router
"""

from typing import List
from fastapi import APIRouter
from packages.schemas.agent import AgentContext
from packages.schemas.decision import TradingDecision
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.pipeline import data_pipeline
from services.debate_service.engine import debate_engine
from services.decision_service.engine import decision_engine
from services.feature_service.pipeline import feature_pipeline
from services.memory_service.memory import memory_service
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector
from services.strategy_service.registry import strategy_registry

router = APIRouter(prefix="/decisions", tags=["Decision Engine"])


@router.get("", response_model=List[TradingDecision])
async def get_recent_decisions():
    return memory_service.short_term_decisions


@router.post("/generate", response_model=TradingDecision)
async def generate_trading_decision(symbol: str = "AAPL"):
    sym = symbol.upper()
    candles = await data_pipeline.ingest_candles(sym, limit=150)
    features = feature_pipeline.compute_features(sym, candles)
    regime = regime_detector.detect_regime(features)
    portfolio_state = portfolio_manager.get_portfolio_state()

    context = AgentContext(
        symbol=sym,
        feature_snapshot=features,
        regime_state=regime,
        portfolio_cash=portfolio_state.cash,
    )

    agent_summary = await agent_orchestrator.run_all_agents(context)
    strat_outputs = strategy_registry.run_all_strategies(context)
    debate_report = debate_engine.conduct_debate(sym, agent_summary, strat_outputs)

    decision = decision_engine.generate_decision(
        symbol=sym,
        feature_snapshot=features,
        regime_state=regime,
        agent_summary=agent_summary,
        strategy_outputs=strat_outputs,
        debate_report=debate_report,
        portfolio_state=portfolio_state,
    )

    memory_service.record_decision(decision)
    return decision
