"""
ATHENA Event-Driven Backtesting Router
"""

from fastapi import APIRouter
from packages.schemas.backtest import BacktestConfig, BacktestResult
from services.backtest_service.engine import backtest_engine

router = APIRouter(prefix="/backtests", tags=["Backtesting"])


@router.post("", response_model=BacktestResult)
async def submit_backtest(config: BacktestConfig):
    return await backtest_engine.run_backtest(config)
