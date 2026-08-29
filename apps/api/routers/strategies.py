"""
ATHENA Quantitative Strategies Router
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException
from packages.schemas.agent import AgentContext
from packages.schemas.strategy import StrategyOutput, StrategyType
from services.data_service.pipeline import data_pipeline
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector
from services.strategy_service.registry import strategy_registry

router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.get("")
async def list_strategies():
    return [
        {
            "id": st_type.value,
            "name": st_type.value.replace("_", " ").title(),
            "description": strat.description,
            "holding_period": strat.default_holding_period,
        }
        for st_type, strat in strategy_registry.strategies.items()
    ]


@router.post("/run-all", response_model=Dict[str, StrategyOutput])
async def run_all_strategies(symbol: str = "AAPL"):
    sym = symbol.upper()
    candles = await data_pipeline.ingest_candles(sym, limit=150)
    features = feature_pipeline.compute_features(sym, candles)
    regime = regime_detector.detect_regime(features)

    context = AgentContext(
        symbol=sym,
        feature_snapshot=features,
        regime_state=regime,
    )
    return strategy_registry.run_all_strategies(context)
