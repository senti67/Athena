"""
ATHENA Portfolio & Capital Allocation Router (INR Native)
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


@router.post("/reset", response_model=PortfolioState)
async def reset_portfolio(initial_cash: float = 1000000.0):
    """Resets the paper portfolio to clean state with 0 positions and specified INR balance."""
    return portfolio_manager.reset_portfolio(initial_cash)


@router.post("/deposit", response_model=PortfolioState)
async def deposit_funds(amount: float):
    """Deposits INR funds into the paper trading portfolio."""
    return portfolio_manager.deposit_cash(amount)


@router.post("/optimize", response_model=TargetAllocation)
async def run_portfolio_optimization(
    symbols: Optional[List[str]] = None,
    objective: OptimizationObjective = OptimizationObjective.MAX_SHARPE,
):
    sym_list = symbols or ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "TATAMOTORS", "SBIN", "NIFTY50"]
    return portfolio_manager.optimize_allocation(sym_list, objective=objective)
