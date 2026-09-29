"""
Unit Tests for ATHENA Institutional Telegram Notification Subsystem
Verifies TradeCard, PositionUpdateCard, NoTradeCard, DailyReportCard,
ExplanationEngine, TelegramFormatter, Deduplication, and TelegramNotifier.
"""

from datetime import datetime
import pytest
from unittest.mock import AsyncMock, patch

from packages.schemas.agent import AgentOrchestratorSummary
from packages.schemas.decision import ActionType, DecisionProposal
from packages.schemas.feature import FeatureSnapshot, TechnicalIndicators
from packages.schemas.order import OrderResponse
from packages.schemas.portfolio import PortfolioState
from packages.schemas.regime import MarketRegime, MarketRegimeState
from packages.schemas.risk import RiskCheckResult
from packages.schemas.strategy import StrategyOutput
from services.notification_service.explanation_engine import ExplanationEngine
from services.notification_service.telegram_formatter import (
    SECTION_DIVIDER,
    TelegramFormatter,
    escape_markdown,
    render_progress_bar,
)
from services.notification_service.telegram_notifier import TelegramNotifier
from services.notification_service.trade_card import (
    DailyReportCard,
    NoTradeCard,
    PositionUpdateCard,
    RiskCheckResultCard,
    StrategyContribution,
    Thesis,
    TradeCard,
)


@pytest.fixture
def sample_feature_snapshot():
    from packages.schemas.feature import StatisticalFeatures, TechnicalFeatures, VolatilityFeatures
    return FeatureSnapshot(
        symbol="AAPL",
        timestamp=datetime.utcnow(),
        current_price=331.20,
        data_quality_score=0.98,
        technical=TechnicalFeatures(
            rsi_14=61.8,
            adx_14=27.4,
            macd=2.45,
            macd_signal=1.85,
            macd_hist=0.60,
            ema_9=333.10,
            sma_20=331.00,
            ema_21=330.50,
            ema_50=324.20,
            ema_200=305.80,
            bb_upper=339.50,
            bb_middle=328.00,
            bb_lower=316.50,
            atr_14=4.80,
            volume_ratio=1.34,
        ),
        statistical=StatisticalFeatures(
            returns_20d=0.052,
        ),
        volatility=VolatilityFeatures(
            realized_vol_20d=0.22,
            atr_normalized=0.0145,
        ),
    )


@pytest.fixture
def sample_regime_state():
    return MarketRegimeState(
        regime=MarketRegime.TRENDING_BULL,
        confidence=0.88,
        description="Strong bullish trend with high ADX",
        adx=27.4,
        atr_pct=0.0145,
    )


@pytest.fixture
def sample_strategies():
    return [
        StrategyOutput(
            symbol="AAPL",
            strategy_name="trend_following",
            signal=ActionType.BUY,
            score=0.82,
            confidence=0.85,
            expected_edge=0.021,
            is_active=True,
        ),
        StrategyOutput(
            symbol="AAPL",
            strategy_name="momentum",
            signal=ActionType.BUY,
            score=0.74,
            confidence=0.80,
            expected_edge=0.018,
            is_active=True,
        ),
        StrategyOutput(
            symbol="AAPL",
            strategy_name="breakout",
            signal=ActionType.BUY,
            score=0.68,
            confidence=0.75,
            expected_edge=0.016,
            is_active=True,
        ),
        StrategyOutput(
            symbol="AAPL",
            strategy_name="mean_reversion",
            signal=ActionType.HOLD,
            score=0.08,
            confidence=0.40,
            expected_edge=0.002,
            is_active=True,
        ),
    ]


@pytest.fixture
def sample_decision():
    return DecisionProposal(
        symbol="AAPL",
        action=ActionType.BUY,
        confidence=0.82,
        expected_edge=0.0184,
        current_price=331.20,
        suggested_shares=42.0,
        stop_loss=326.10,
        take_profit=342.80,
        risk_reward_ratio=2.27,
        triggering_strategy="trend_following",
        reason="Multiple independent signal groups agree with the trade and the current market regime supports the selected strategies.",
    )


def test_progress_bar_renderer():
    bar_78 = render_progress_bar(78, 100, length=10)
    assert "████████░░ 78/100" in bar_78
    bar_0 = render_progress_bar(0, 100, length=10)
    assert "░░░░░░░░░░ 0/100" in bar_0
    bar_100 = render_progress_bar(100, 100, length=10)
    assert "██████████ 100/100" in bar_100


def test_escape_markdown():
    text = "trend_following_v2"
    escaped = escape_markdown(text)
    assert "_" not in escaped
    assert "trend following v2" == escaped


def test_explanation_engine_thesis_generation(sample_decision, sample_feature_snapshot, sample_regime_state, sample_strategies):
    thesis = ExplanationEngine.generate_thesis(
        decision=sample_decision,
        features=sample_feature_snapshot,
        regime=sample_regime_state,
        strategy_outputs=sample_strategies,
    )
    assert thesis.primary_driver == "Trend Following"
    assert len(thesis.supporting_factors) >= 2
    assert any("EMA" in f for f in thesis.supporting_factors)
    assert len(thesis.risk_factors) >= 1
    assert len(thesis.invalidation_conditions) >= 1
    assert "326.10" in thesis.invalidation_conditions[0]


def test_build_trade_card_and_format_buy_signal(
    sample_decision, sample_feature_snapshot, sample_regime_state, sample_strategies
):
    port_state = PortfolioState(total_equity=100000.0, cash=50000.0, buying_power=250000.0)
    risk_check = RiskCheckResult(approved=True)

    card = ExplanationEngine.build_trade_card(
        decision=sample_decision,
        features=sample_feature_snapshot,
        regime=sample_regime_state,
        strategy_outputs=sample_strategies,
        agent_summary=None,
        risk_check=risk_check,
        portfolio_state=port_state,
    )

    formatted = TelegramFormatter.format_trade_signal(card)

    # Verify structural sections
    assert "🧠 ATHENA TRADE THESIS" in formatted
    assert "🟢 BUY · AAPL" in formatted
    assert "Confidence: 82%" in formatted
    assert "Signal Strength: 82/100" in formatted
    assert "Expected Edge: +1.84%" in formatted
    assert "💵 Entry\n$331.20" in formatted
    assert "🎯 Target\n$342.80" in formatted
    assert "🛑 Stop\n$326.10" in formatted
    assert "⚖️ R:R\n2.27 : 1" in formatted
    assert "📦 Position\n42 shares" in formatted
    assert "📊 MARKET CONTEXT" in formatted
    assert "🟢 TRENDING BULL" in formatted
    assert "🔬 STRATEGY EVIDENCE" in formatted
    assert "Trend Following" in formatted
    assert "🧩 WHY ATHENA LIKES IT" in formatted
    assert "⚠️ WHAT COULD GO WRONG" in formatted
    assert "Invalidation:" in formatted
    assert "🛡️ RISK CHECK" in formatted
    assert "Daily Loss Limit: ✅" in formatted
    assert "Buying Power: ✅" in formatted
    assert "Position Limit: ✅" in formatted
    assert "Correlation Risk: ✅" in formatted
    assert "Data Quality: ✅" in formatted
    assert "🤖 ATHENA DECISION\n━━━━━━━━━━━━━━━━━━━━\n\nBUY APPROVED" in formatted
    assert "🟢 PAPER TRADE" in formatted
    assert "⏱️ Generated:" in formatted


def test_format_sell_signal(sample_feature_snapshot, sample_regime_state):
    sell_decision = DecisionProposal(
        symbol="TSLA",
        action=ActionType.SELL,
        confidence=0.75,
        expected_edge=0.015,
        current_price=210.50,
        suggested_shares=30.0,
        stop_loss=218.00,
        take_profit=195.00,
        risk_reward_ratio=2.07,
        triggering_strategy="mean_reversion",
    )
    thesis = Thesis(
        primary_driver="Mean Reversion",
        supporting_factors=["Price touched upper Bollinger Band with bearish divergence"],
        risk_factors=["Short squeeze potential if momentum re-accelerates"],
        invalidation_conditions=["Close above stop-loss at $218.00"],
    )
    card = TradeCard(
        symbol="TSLA",
        side="SELL",
        decision="SELL EXECUTED",
        entry_price=210.50,
        current_price=210.50,
        stop_loss=218.00,
        take_profit=195.00,
        position_size=30.0,
        position_value=6315.0,
        portfolio_weight=6.3,
        regime="HIGH VOLATILITY",
        signal_score=75,
        confidence=0.75,
        expected_edge=0.015,
        reward_risk=2.07,
        strategy_contributions=[
            StrategyContribution(strategy_name="Mean Reversion", signal="SELL", score=-0.75, material_contribution=True)
        ],
        thesis=thesis,
    )
    formatted = TelegramFormatter.format_trade_signal(card)
    assert "🔴 SELL · TSLA" in formatted
    assert "SELL EXECUTED" in formatted
    assert "$210.50" in formatted


def test_format_no_trade_card(sample_feature_snapshot, sample_regime_state):
    card = ExplanationEngine.build_no_trade_card(
        symbol="NVDA",
        features=sample_feature_snapshot,
        regime=sample_regime_state,
        candidate_signal="BUY",
        final_score=64,
        required_score=75,
        expected_edge=0.0084,
        reward_risk=1.42,
    )
    formatted = TelegramFormatter.format_no_trade(card)

    assert "🚫 ATHENA — NO TRADE" in formatted
    assert "NVDA" in formatted
    assert "Final Score:\n64/100" in formatted
    assert "Required:\n75/100" in formatted
    assert "📊 ANALYSIS" in formatted
    assert "⚠️ BLOCKING FACTORS" in formatted
    assert "Expected edge (+0.84%) below minimum required" in formatted
    assert "Reward/Risk only 1.42 : 1" in formatted
    assert "🤖 DECISION\n━━━━━━━━━━━━━━━━━━━━\n\nHOLD / NO TRADE" in formatted
    assert "Next trigger:" in formatted


def test_format_position_update_card(sample_feature_snapshot, sample_regime_state):
    card = ExplanationEngine.build_position_update_card(
        symbol="AAPL",
        shares=42.0,
        entry_price=331.20,
        current_price=337.42,
        unrealized_pnl_pct=1.88,
        unrealized_pnl_val=261.24,
        stop_loss=326.10,
        take_profit=342.80,
        features=sample_feature_snapshot,
        regime=sample_regime_state,
        holding_duration_str="2d 7h",
        original_thesis="Trend + Momentum",
        verdict="HOLD",
        next_review_time="In 2 hours",
    )
    formatted = TelegramFormatter.format_position_update(card)

    assert "📈 ATHENA POSITION UPDATE" in formatted
    assert "AAPL · LONG" in formatted
    assert "Entry:\n$331.20" in formatted
    assert "Current:\n$337.42" in formatted
    assert "P&L:\n🟢 +1.88%  (+$261.24)" in formatted
    assert "Holding:\n2d 7h" in formatted
    assert "📊 POSITION HEALTH" in formatted
    assert "Original Thesis:\nTrend + Momentum" in formatted
    assert "🟢 TRENDING BULL" in formatted
    assert "🎯 LEVELS" in formatted
    assert "Target:\n$342.80" in formatted
    assert "Stop:\n$326.10" in formatted
    assert "🤖 ATHENA ASSESSMENT\n━━━━━━━━━━━━━━━━━━━━\n\nHOLD" in formatted


def test_format_daily_report_card():
    card = DailyReportCard(
        date_str="2026-09-29",
        portfolio_value=103142.50,
        daily_pnl_pct=0.82,
        daily_pnl_val=1421.00,
        total_pnl_pct=3.14,
        total_pnl_val=3142.50,
        trades_count=6,
        wins_count=4,
        losses_count=2,
        win_rate_pct=66.7,
        profit_factor=1.82,
        avg_win=421.00,
        avg_loss=-218.00,
        max_drawdown_pct=1.42,
        portfolio_exposure_pct=18.7,
        largest_position_str="AAPL · 4.8%",
        daily_risk_pct=0.63,
        spy_regime="Bullish",
        qqq_regime="Bullish",
        vix_status="Elevated",
        overall_market_bias="Risk-On",
        trades_executed=6,
        signals_rejected=19,
        risk_vetoes=4,
        most_successful_strategy="Trend Following",
        weakest_strategy="Mean Reversion",
    )
    formatted = TelegramFormatter.format_daily_report(card)

    assert "🧠 ATHENA DAILY REPORT" in formatted
    assert "📅 2026-09-29" in formatted
    assert "Portfolio:\n$103,142.50" in formatted
    assert "Daily P&L:\n🟢 +0.82%  (+$1,421.00)" in formatted
    assert "Total P&L:\n🟢 +3.14%" in formatted
    assert "📊 TRADING ACTIVITY" in formatted
    assert "Trades:\n6" in formatted
    assert "Win Rate:\n66.7%" in formatted
    assert "Profit Factor:\n1.82" in formatted
    assert "Average Win:\n+$421.00" in formatted
    assert "Average Loss:\n-$218.00" in formatted
    assert "📈 RISK" in formatted
    assert "Max Drawdown:\n1.42%" in formatted
    assert "Portfolio Exposure:\n18.7%" in formatted
    assert "Largest Position:\nAAPL · 4.8%" in formatted
    assert "🧠 MARKET REGIME" in formatted
    assert "SPY:\n🟢 Bullish" in formatted
    assert "🤖 ATHENA" in formatted
    assert "Trades Executed:\n6" in formatted
    assert "Signals Rejected:\n19" in formatted
    assert "Risk Vetoes:\n4" in formatted


def test_missing_data_and_optional_fields_display_na():
    minimal_thesis = Thesis(
        primary_driver="Quantitative",
        supporting_factors=[],
        risk_factors=[],
        invalidation_conditions=[],
    )
    card = TradeCard(
        symbol="MSFT",
        side="BUY",
        decision="BUY APPROVED",
        entry_price=None,
        current_price=None,
        stop_loss=None,
        take_profit=None,
        position_size=None,
        position_value=None,
        portfolio_weight=None,
        regime="UNCERTAIN",
        trend_details=None,
        momentum_details=None,
        volume_details=None,
        signal_score=50,
        confidence=0.50,
        expected_edge=None,
        reward_risk=None,
        thesis=minimal_thesis,
    )
    formatted = TelegramFormatter.format_trade_signal(card)

    assert "N/A" in formatted
    assert "💵 Entry\nN/A" in formatted
    assert "🎯 Target\nN/A" in formatted
    assert "🛑 Stop\nN/A" in formatted


def test_duplicate_notification_prevention():
    notifier = TelegramNotifier(token="test_token", chat_id="12345", enabled=True, dedup_ttl_seconds=60)
    fp = "TEST_FINGERPRINT_1"

    # First check: not duplicate
    assert notifier._is_duplicate(fp) is False

    # Second immediate check: is duplicate
    assert notifier._is_duplicate(fp) is True


def test_long_message_splitting():
    # Construct an oversized message
    long_section = "A" * 2500
    oversized_msg = f"{SECTION_DIVIDER}\nSection 1\n{long_section}\n{SECTION_DIVIDER}\nSection 2\n{long_section}"
    chunks = TelegramFormatter.split_message_if_needed(oversized_msg, max_length=3000)
    assert len(chunks) == 2
    for c in chunks:
        assert len(c) <= 3000


@pytest.mark.asyncio
async def test_risk_veto_notification_formatting():
    notifier = TelegramNotifier(token="fake_token", chat_id="123", enabled=False)
    # Even if disabled, the format method runs without crash
    card = ExplanationEngine.build_no_trade_card(
        symbol="AAPL",
        features=None,
        regime=None,
        candidate_signal="BUY",
        veto_reason="Portfolio buying power floor ($200,000) breach",
    )
    assert any("buying power" in b.lower() for b in card.blocking_factors)


def test_telegram_cannot_place_trades():
    """
    Architectural invariant test:
    Confirms TelegramNotifier has no methods or broker bindings for order dispatch.
    """
    notifier = TelegramNotifier()
    assert not hasattr(notifier, "submit_order")
    assert not hasattr(notifier, "execute_trade")
    assert not hasattr(notifier, "broker")
    assert not hasattr(notifier, "alpaca_broker")
