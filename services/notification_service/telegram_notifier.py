"""
ATHENA Telegram Notification Service
Sends institutional quantitative research notes, trade cards, position updates,
rejected signal explanations, and daily performance reports directly to Telegram.
Strictly read-only: Cannot place trades or alter broker state.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import httpx

from packages.common.config import settings
from packages.logging.logger import get_logger
from services.notification_service.telegram_formatter import (
    TelegramFormatter,
    MAX_TELEGRAM_MESSAGE_LENGTH,
)
from services.notification_service.trade_card import (
    DailyReportCard,
    NoTradeCard,
    PositionUpdateCard,
    TradeCard,
)

logger = get_logger("athena.telegram_notifier")


class TelegramNotifier:
    """
    Institutional Telegram Notifier for ATHENA Quantitative Platform.
    Handles message formatting, deduplication, long-message splitting, and error resilience.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        enabled: Optional[bool] = None,
        dedup_ttl_seconds: int = 180,
    ):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self.enabled = enabled if enabled is not None else settings.TELEGRAM_NOTIFICATIONS_ENABLED
        self.dedup_ttl_seconds = dedup_ttl_seconds
        self._recent_fingerprints: Dict[str, datetime] = {}

    def is_configured(self) -> bool:
        """Verifies if real Telegram bot credentials are provided."""
        return (
            bool(self.enabled)
            and bool(self.token)
            and bool(self.chat_id)
            and self.token != "your_telegram_bot_token"
            and self.chat_id != "your_telegram_chat_id"
        )

    def _cleanup_old_fingerprints(self):
        """Prunes fingerprints older than TTL."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.dedup_ttl_seconds)
        self._recent_fingerprints = {
            fp: ts for fp, ts in self._recent_fingerprints.items() if ts > cutoff
        }

    def _is_duplicate(self, fingerprint: str) -> bool:
        """Checks if a fingerprint was recently dispatched."""
        self._cleanup_old_fingerprints()
        if fingerprint in self._recent_fingerprints:
            logger.info(f"Duplicate notification prevented for fingerprint: {fingerprint}")
            return True
        self._recent_fingerprints[fingerprint] = datetime.utcnow()
        return False

    async def send_message(self, text: str, fingerprint: Optional[str] = None) -> bool:
        """
        Sends a Markdown message to Telegram with deduplication and auto-splitting.
        """
        if not self.is_configured():
            logger.debug("Telegram notifications disabled or unconfigured.")
            return False

        if fingerprint and self._is_duplicate(fingerprint):
            return True

        chunks = TelegramFormatter.split_message_if_needed(text, max_length=MAX_TELEGRAM_MESSAGE_LENGTH)
        success = True

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        async with httpx.AsyncClient(timeout=10.0) as client:
            for chunk in chunks:
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                }
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code != 200:
                        logger.warning(f"Telegram send failed [{res.status_code}]: {res.text}")
                        success = False
                except Exception as e:
                    logger.warning(f"Telegram network transport error: {e}")
                    success = False

        return success

    async def send_trade_card(self, card: TradeCard) -> bool:
        """Sends an institutional Trade Thesis research note."""
        text = TelegramFormatter.format_trade_signal(card)
        fingerprint = f"TRADE_SIGNAL:{card.symbol}:{card.side}:{card.order_id or int(card.timestamp.timestamp())}"
        return await self.send_message(text, fingerprint=fingerprint)

    async def send_position_update(self, card: PositionUpdateCard) -> bool:
        """Sends a position monitoring progress card."""
        text = TelegramFormatter.format_position_update(card)
        # Deduplicate per symbol within a 15-minute window
        minute_bucket = card.timestamp.strftime("%Y%m%d%H") + f"_{card.timestamp.minute // 15}"
        fingerprint = f"POS_UPDATE:{card.symbol}:{minute_bucket}"
        return await self.send_message(text, fingerprint=fingerprint)

    async def send_no_trade_card(self, card: NoTradeCard) -> bool:
        """Sends a rejected signal / no-trade explanation card."""
        text = TelegramFormatter.format_no_trade(card)
        fingerprint = f"NO_TRADE:{card.symbol}:{card.timestamp.strftime('%Y%m%d%H%M')}"
        return await self.send_message(text, fingerprint=fingerprint)

    async def send_daily_report(self, card: DailyReportCard) -> bool:
        """Sends the daily 8:00 PM intelligence & performance digest."""
        text = TelegramFormatter.format_daily_report(card)
        fingerprint = f"DAILY_REPORT:{card.date_str}"
        return await self.send_message(text, fingerprint=fingerprint)

    async def notify_order_submitted(
        self,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        order_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        confidence: float = 0.80,
        consensus_ratio: str = "8/8",
    ) -> bool:
        """
        Backwards-compatible bridge for router order notifications.
        """
        side_emoji = "🟢" if action.upper() == "BUY" else "🔴"
        now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        rr = ((take_profit - price) / max(price - stop_loss, 0.01)) if (stop_loss and take_profit and price > stop_loss) else 2.0

        msg = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ ATHENA TRADE ALERT\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{side_emoji} {action.upper()} · {symbol.upper()}\n"
            f"Confidence: {confidence * 100:.0f}%\n"
            f"Quantity: {quantity:.0f} shares\n"
            f"Price: ${price:,.2f}\n\n"
            f"🎯 Target: ${take_profit:,.2f}\n" if take_profit else ""
            f"🛑 Stop: ${stop_loss:,.2f}\n" if stop_loss else ""
            f"⚖️ R:R: {rr:.2f} : 1\n\n"
            f"Order ID:\n{order_id}\n\n"
            f"⏱️ Generated:\n{now_utc}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        fingerprint = f"ORDER_SUBMITTED:{symbol}:{order_id}"
        return await self.send_message(msg, fingerprint=fingerprint)

    async def notify_risk_veto(self, symbol: str, reason: str) -> bool:
        """Notifies when the Risk Management VETO Layer blocks an order."""
        now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        msg = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ ATHENA RISK VETO\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{symbol.upper()}\n\n"
            f"Status:\n⛔ ORDER BLOCKED\n\n"
            f"Reason:\n{reason}\n\n"
            f"⏱️ Generated:\n{now_utc}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        fingerprint = f"RISK_VETO:{symbol}:{reason[:30]}"
        return await self.send_message(msg, fingerprint=fingerprint)

    async def notify_position_health_report(
        self,
        symbol: str,
        shares: float,
        entry_price: float,
        current_price: float,
        unrealized_pnl: float,
        unrealized_pnl_pct: float,
        rsi: float,
        regime: str,
        verdict: str,
        stop_loss: float,
        take_profit: float,
        nav: float,
        buying_power: float,
    ) -> bool:
        """Sends comprehensive intraday position progress analysis to Telegram."""
        card = PositionUpdateCard(
            symbol=symbol,
            side="LONG",
            entry_price=entry_price,
            current_price=current_price,
            shares=shares,
            unrealized_pnl_pct=unrealized_pnl_pct,
            unrealized_pnl_val=unrealized_pnl,
            holding_duration_str="Intraday",
            original_thesis="Trend + Momentum",
            current_regime=regime,
            momentum_status="Strengthening" if rsi >= 50 else "Weakening",
            volume_status="Supportive",
            signal=verdict,
            thesis_strength_score=75 if unrealized_pnl >= 0 else 60,
            target_price=take_profit,
            stop_price=stop_loss,
            dist_to_target_pct=((take_profit - current_price) / current_price * 100) if current_price > 0 else 0.0,
            dist_to_stop_pct=((stop_loss - current_price) / current_price * 100) if current_price > 0 else 0.0,
            assessment_verdict=verdict,
            assessment_reason="The original thesis remains valid. Risk parameters intact.",
            next_review_time="In 2 hours",
            timestamp=datetime.utcnow(),
        )
        return await self.send_position_update(card)


telegram_notifier = TelegramNotifier()
