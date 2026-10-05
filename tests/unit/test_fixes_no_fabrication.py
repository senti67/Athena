"""Regression tests for the "fix" pass: no fabricated broker/account data, no fabricated report values."""

import pytest

from packages.common.exceptions import BrokerConnectionException
from services.execution_service.alpaca_broker import AlpacaBroker
from services.notification_service.telegram_formatter import TelegramFormatter
from services.notification_service.telegram_notifier import TelegramNotifier
from services.notification_service.trade_card import DailyReportCard


def _real_cred_broker():
    # Credentials that pass _has_valid_credentials() but point at an unreachable host.
    return AlpacaBroker(
        api_key="PKREALLOOKINGKEY",
        secret_key="realLookingSecret",
        base_url="http://127.0.0.1:9/paper-api",  # nothing listens here -> connection error
    )


@pytest.mark.asyncio
async def test_unreachable_broker_raises_instead_of_fake_account():
    broker = _real_cred_broker()
    broker.base_url = "http://127.0.0.1:9/paper-api"
    broker.PAPER_BASE_URL = "http://127.0.0.1:9/paper-api"
    with pytest.raises(BrokerConnectionException):
        await broker.get_account()
    with pytest.raises(BrokerConnectionException):
        await broker.get_positions()
    with pytest.raises(BrokerConnectionException):
        await broker.get_open_orders()


def test_daily_report_unmeasured_metrics_render_na():
    card = DailyReportCard(date_str="2026-10-05", portfolio_value=98000.0)
    text = TelegramFormatter.format_daily_report(card)
    for label in ("Daily P&L:\nN/A", "Profit Factor:\nN/A", "Max Drawdown:\nN/A",
                  "Trades Executed:\nN/A", "Most Successful Strategy:\nN/A", "SPY:\nN/A", "VIX:\nN/A"):
        assert label in text
    # none of the old made-up values may appear
    for fake in ("2.15", "+$350", "0.85%", "Trend Following", "Risk-On"):
        assert fake not in text


@pytest.mark.asyncio
async def test_order_alert_message_has_all_sections(monkeypatch):
    sent = []
    n = TelegramNotifier(token="t", chat_id="c", enabled=True)

    async def fake_send(text, fingerprint=None):
        sent.append(text)
        return True

    monkeypatch.setattr(n, "send_message", fake_send)
    await n.notify_order_submitted("AAPL", "BUY", 10, 100.0, "OID-1", stop_loss=95.0, take_profit=110.0)
    msg = sent[0]
    assert "BUY · AAPL" in msg and "Target: $110.00" in msg and "Stop: $95.00" in msg
    assert "R:R: 2.00 : 1" in msg and "OID-1" in msg
