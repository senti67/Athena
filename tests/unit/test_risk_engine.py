"""
Unit Tests for Independent Risk Management, Cost Analyzer, Compliance & Position Sizer
"""

from packages.common.config import settings
from packages.schemas.decision import ActionType, TradingDecision
from packages.schemas.portfolio import PortfolioState
from services.risk_service.engine import RiskEngine
from services.risk_service.cost_analyzer import TransactionCostAnalyzer
from services.risk_service.compliance import ComplianceEngine
from services.risk_service.position_sizer import PositionSizer


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
        validation_status="VALIDATED",
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
        validation_status="VALIDATED",
        reasoning="Test decision",
    )

    result = engine.evaluate_decision(decision, state)
    assert result.approved is False, "Emergency kill switch must veto all orders"
    assert result.kill_switch_triggered is True

    # Reset kill switch
    engine.reset_kill_switch()
    assert engine.kill_switch_active is False


def test_buying_power_reserve_floor():
    """Verifies that the buying power reserve floor is strictly enforced."""
    engine = RiskEngine()
    # Large account with cash above floor
    state = PortfolioState(nav=250000.0, cash=210000.0)
    # Order worth $20,000 -> would leave $190,000 cash (< $200k floor)
    decision = TradingDecision(
        id="test-dec-bp",
        symbol="AAPL",
        action=ActionType.BUY,
        confidence=0.85,
        current_price=200.0,
        suggested_shares=100,  # $20,000 order
        stop_loss=190.0,
        take_profit=220.0,
        risk_reward_ratio=2.0,
        validation_status="VALIDATED",
        reasoning="Test floor",
    )

    result = engine.evaluate_decision(decision, state)
    assert result.approved is False
    assert any("MIN_BUYING_POWER_RESERVE_FLOOR" in v.rule_name for v in result.violations)


def test_transaction_cost_analyzer():
    cost_analyzer = TransactionCostAnalyzer(max_cost_to_return_ratio=0.35)
    # Reasonable trade
    res_pass = cost_analyzer.evaluate_cost(
        symbol="AAPL", price=200.0, shares=50, expected_return_pct=0.04, bid_ask_spread_bps=2.0
    )
    assert res_pass.status in ("PASS", "WARN")

    # Extreme spread friction (spread 200 bps on a 1% expected gain)
    res_reject = cost_analyzer.evaluate_cost(
        symbol="ILLIQ", price=10.0, shares=1000, expected_return_pct=0.01, bid_ask_spread_bps=200.0
    )
    assert res_reject.status == "REJECT"


def test_compliance_engine():
    comp = ComplianceEngine(min_stock_price=5.0, restricted_symbols=["RESTRICTED"])
    # Valid equity
    res_valid = comp.check_compliance("AAPL", 200.0, "BUY")
    assert res_valid.is_compliant is True

    # Penny stock rejection
    res_penny = comp.check_compliance("PENNY", 1.50, "BUY")
    assert res_penny.is_compliant is False
    assert any("Penny stock" in v for v in res_penny.violations)

    # Restricted stock rejection
    res_restr = comp.check_compliance("RESTRICTED", 50.0, "BUY")
    assert res_restr.is_compliant is False


def test_position_sizer():
    sizer = PositionSizer()
    res = sizer.calculate_position_size(
        symbol="AAPL",
        current_price=200.0,
        atr_14=4.0,
        portfolio_nav=500000.0,
        available_cash=300000.0,
        confidence=0.85,
    )
    assert res["shares"] > 0
    assert res["notional_usd"] <= 25000.0  # Max position cap check
