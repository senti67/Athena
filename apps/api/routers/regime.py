"""
ATHENA Market Regime Router
"""

from fastapi import APIRouter
from packages.schemas.regime import RegimeState
from services.data_service.pipeline import data_pipeline
from services.feature_service.pipeline import feature_pipeline
from services.regime_service.detector import regime_detector

router = APIRouter(prefix="/regime", tags=["Market Regime"])


@router.get("/current", response_model=RegimeState)
async def get_current_regime(symbol: str = "SPY"):
    sym = symbol.upper()
    candles = await data_pipeline.ingest_candles(sym, limit=150)
    features = feature_pipeline.compute_features(sym, candles)
    return regime_detector.detect_regime(features)
