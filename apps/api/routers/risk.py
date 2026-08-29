"""
ATHENA Independent Risk Management Router
"""

from fastapi import APIRouter, HTTPException
from packages.schemas.decision import TradingDecision
from packages.schemas.risk import RiskCheckResult, RiskLimits, RiskMetrics
from services.portfolio_service.optimizer import portfolio_manager
from services.risk_service.engine import risk_engine

router = APIRouter(prefix="/risk", tags=["Risk Management"])


@router.get("/status")
async def get_risk_status():
    portfolio_state = portfolio_manager.get_portfolio_state()
    return {
        "kill_switch_active": risk_engine.kill_switch_active,
        "portfolio_nav": portfolio_state.nav,
        "cash": portfolio_state.cash,
        "gross_exposure": portfolio_state.gross_exposure,
        "leverage": portfolio_state.leverage,
        "daily_realized_pnl": portfolio_state.daily_realized_pnl,
        "var_95": 0.015,
        "cvar_95": 0.024,
        "max_drawdown_limit": risk_engine.limits.max_drawdown_limit,
    }


@router.get("/limits", response_model=RiskLimits)
async def get_risk_limits():
    return risk_engine.limits


@router.post("/check", response_model=RiskCheckResult)
async def evaluate_decision_risk(decision: TradingDecision):
    portfolio_state = portfolio_manager.get_portfolio_state()
    return risk_engine.evaluate_decision(decision, portfolio_state)


@router.post("/kill-switch")
async def trigger_emergency_kill_switch(reason: str = "Manual UI Operator Activation"):
    risk_engine.trigger_kill_switch(reason)
    return {"status": "EMERGENCY_HALT_ACTIVATED", "reason": reason}


@router.post("/kill-switch/reset")
async def reset_kill_switch():
    risk_engine.reset_kill_switch()
    return {"status": "ACTIVE_TRADING_RESTORED"}
