"""
ATHENA Portfolio & Capital Allocation Router
"""

from typing import Dict, List, Optional
from fastapi import APIRouter
from packages.schemas.portfolio import (
    OptimizationObjective,
    PortfolioState,
    Position,
    TargetAllocation,
)
from services.portfolio_service.optimizer import portfolio_manager

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioState)
async def get_portfolio():
    return portfolio_manager.get_portfolio_state()


@router.get("/positions", response_model=Dict[str, Position])
async def get_positions():
    return portfolio_manager.get_portfolio_state().positions


@router.post("/optimize", response_model=TargetAllocation)
async def run_portfolio_optimization(
    symbols: Optional[List[str]] = None,
    objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
):
    sym_list = symbols or ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "SPY"]
    return portfolio_manager.optimize_allocation(sym_list, objective=objective)
