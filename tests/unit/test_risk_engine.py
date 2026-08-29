"""
Unit Tests for Independent Risk Management VETO Layer
"""

from packages.schemas.decision import ActionType, TradingDecision
from packages.schemas.portfolio import PortfolioState
from services.risk_service.engine import RiskEngine


def test_risk_veto_on_excessive_loss():
    engine = RiskEngine()
    state = PortfolioState(
        nav=100000.0,
        cash=100000.0,
        daily_realized_pnl=-5500.0,  # exceeds $5,000 max daily loss
    )
    decision = TradingDecision(
        id="test-dec-01",
        symbol="AAPL",
        action=ActionType.BUY,
        confidence=0.85,
        current_price=200.0,
        suggested_shares=20,
        stop_loss=190.0,
        take_profit=220.0,
        risk_reward_ratio=2.0,
        reasoning="Test decision",
    )

    result = engine.evaluate_decision(decision, state)
    assert result.approved is False, "Trade MUST be vetoed when daily loss breaches limit"
    assert "MAX_DAILY_LOSS" in [v.rule_name for v in result.violations]


def test_kill_switch_blocks_all_trading():
    engine = RiskEngine()
    engine.trigger_kill_switch("Manual test shutdown")
    state = PortfolioState(nav=100000.0, cash=100000.0)

    decision = TradingDecision(
        id="test-dec-02",
        symbol="AAPL",
        action=ActionType.BUY,
        confidence=0.95,
        current_price=200.0,
        suggested_shares=10,
        stop_loss=190.0,
        take_profit=220.0,
        risk_reward_ratio=2.0,
        reasoning="Test decision",
    )

    result = engine.evaluate_decision(decision, state)
    assert result.approved is False, "Emergency kill switch must veto all orders"
    assert result.kill_switch_triggered is True

    # Reset kill switch
    engine.reset_kill_switch()
    assert engine.kill_switch_active is False
