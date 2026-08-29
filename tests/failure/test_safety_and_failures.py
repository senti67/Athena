"""
Failure-Injection & Safety Boundary Tests for ATHENA
"""

from datetime import datetime
import pytest
from packages.common.exceptions import (
    DataQualityException,
    LiveTradingDisabledException,
    RiskVetoException,
)
from packages.schemas.decision import ActionType, TradingDecision
from packages.schemas.market import Candle
from packages.schemas.order import ExecutionMode, OrderRequest, OrderSide, OrderType
from packages.schemas.portfolio import PortfolioState
from packages.schemas.risk import RiskCheckResult
from services.data_service.quality import DataQualityAgent
from services.execution_service.live_broker import LiveBrokerAdapter
from services.execution_service.router import ExecutionRouter
from services.risk_service.engine import RiskEngine


@pytest.mark.asyncio
async def test_live_trading_refused_when_disabled():
    adapter = LiveBrokerAdapter()
    adapter.is_enabled = False  # Guarantee false

    request = OrderRequest(
        client_order_id="TEST-LIVE-ORDER-01",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=10.0,
        execution_mode=ExecutionMode.LIVE,
    )

    with pytest.raises(LiveTradingDisabledException):
        await adapter.submit_order(request)


def test_data_quality_rejection_on_impossible_prices():
    agent = DataQualityAgent(min_quality_score=0.80)
    # Impossible negative candle
    corrupted_candles = [
        Candle(
            symbol="AAPL",
            timestamp=datetime.utcnow(),
            open=100.0,
            high=105.0,
            low=-5.0,  # Impossible negative price
            close=98.0,
            volume=10000.0,
        )
    ]
    report = agent.evaluate_candles("AAPL", corrupted_candles)
    assert report.is_valid is False
    assert report.data_quality_score < 0.80


@pytest.mark.asyncio
async def test_execution_router_blocks_when_risk_vetoes():
    router = ExecutionRouter()
    decision = TradingDecision(
        id="vetoed-dec",
        symbol="AAPL",
        action=ActionType.BUY,
        confidence=0.80,
        current_price=200.0,
        suggested_shares=50,
        stop_loss=190.0,
        take_profit=220.0,
        reasoning="Test",
    )
    vetoed_risk_check = RiskCheckResult(
        check_id="chk-01",
        decision_id="vetoed-dec",
        symbol="AAPL",
        action="BUY",
        approved=False,
        risk_score=0.95,
        veto_reason="Portfolio maximum leverage exceeded",
    )

    with pytest.raises(RiskVetoException):
        await router.execute_trade(decision, vetoed_risk_check, mode=ExecutionMode.PAPER)
