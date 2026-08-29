"""
ATHENA Orders & Deterministic Execution Router
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from packages.schemas.decision import TradingDecision
from packages.schemas.order import ExecutionMode, OrderRequest, OrderResponse
from services.execution_service.router import execution_router
from services.journal_service.journal import journal_service
from services.portfolio_service.optimizer import portfolio_manager
from services.risk_service.engine import risk_engine

router = APIRouter(prefix="/orders", tags=["Orders & Execution"])


@router.get("", response_model=List[OrderResponse])
async def list_orders():
    return list(execution_router.paper_broker.orders.values())


@router.post("/execute-decision", response_model=Optional[OrderResponse])
async def execute_decision_pipeline(
    decision: TradingDecision,
    mode: ExecutionMode = ExecutionMode.PAPER,
):
    """
    Executes a structured trading decision through the full deterministic pipeline:
    Decision -> Risk Veto -> Order Creation -> Paper/Live Broker -> Portfolio & Journal update.
    """
    portfolio_state = portfolio_manager.get_portfolio_state()
    risk_check = risk_engine.evaluate_decision(decision, portfolio_state)

    if not risk_check.approved:
        raise HTTPException(
            status_code=400,
            detail=f"RISK VETO: {risk_check.veto_reason}. Execution rejected.",
        )

    order_response = await execution_router.execute_trade(decision, risk_check, mode=mode)
    if order_response:
        journal_service.record_entry(decision, risk_check, order_response)

    return order_response


@router.post("/paper", response_model=OrderResponse)
async def submit_paper_order(order: OrderRequest):
    return await execution_router.paper_broker.submit_order(order)


@router.post("/live", response_model=OrderResponse)
async def submit_live_order(order: OrderRequest):
    return await execution_router.live_broker.submit_order(order)
