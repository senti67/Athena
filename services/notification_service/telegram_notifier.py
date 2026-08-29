"""
ATHENA Telegram Notification & Alert Service
Sends real-time trade signals, executions, risk vetoes, and portfolio updates directly to your Telegram chat.
"""

import asyncio
from datetime import datetime
from typing import Optional
import httpx

from packages.common.config import settings
from packages.logging.logger import get_logger

logger = get_logger("athena.telegram_notifier")


class TelegramNotifier:
    """
    Dedicated Telegram Bot Notifier for ATHENA Multi-Agent Quantitative Platform.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self.enabled = enabled if enabled is not None else settings.TELEGRAM_NOTIFICATIONS_ENABLED

    def is_configured(self) -> bool:
        return (
            bool(self.enabled)
            and bool(self.token)
            and bool(self.chat_id)
            and self.token != "your_telegram_bot_token"
            and self.chat_id != "your_telegram_chat_id"
        )

    async def send_message(self, text: str) -> bool:
        """Sends a formatted Markdown message to the configured Telegram chat."""
        if not self.is_configured():
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return True
                else:
                    logger.warning(f"Telegram send failed: {res.status_code} {res.text}")
                    return False
            except Exception as e:
                logger.warning(f"Telegram network error: {e}")
                return False

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
        consensus_ratio: str = "14/14",
    ):
        """Notifies when a new order is dispatched to the broker."""
        action_emoji = "🟢 *BUY*" if action.upper() == "BUY" else "🔴 *SELL*"
        now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        msg = (
            f"⚡ *ATHENA Multi-Agent Trade Alert* ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Asset*: `{symbol}`\n"
            f"• *Signal*: {action_emoji}\n"
            f"• *Quantity*: `{quantity:.0f}` shares\n"
            f"• *Price*: `${price:,.2f}`\n"
            f"• *AI Consensus*: `{confidence*100:.0f}%` ({consensus_ratio} Agents)\n"
        )
        if stop_loss and take_profit:
            rr = (take_profit - price) / max(price - stop_loss, 0.01) if action.upper() == "BUY" else 2.0
            msg += (
                f"• *Target (TP)*: `${take_profit:,.2f}`\n"
                f"• *Stop Loss (SL)*: `${stop_loss:,.2f}`\n"
                f"• *Reward / Risk*: `{rr:.1f} : 1`\n"
            )
        msg += (
            f"• *Order ID*: `{order_id}`\n"
            f"• *Time*: `{now_utc}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 [View Live on Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)"
        )

        await self.send_message(msg)

    async def notify_risk_veto(self, symbol: str, reason: str):
        """Notifies when the Risk Management VETO Layer blocks an order."""
        msg = (
            f"🛡️ *ATHENA Risk Management VETO* 🛡️\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Asset*: `{symbol}`\n"
            f"• *Status*: ⛔ *ORDER BLOCKED*\n"
            f"• *Reason*: _{reason}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 _Institutional capital preservation rule enforced._"
        )
        await self.send_message(msg)

    async def notify_daily_summary(
        self,
        nav: float,
        cash: float,
        trades_count: int,
        positions_count: int,
    ):
        """Sends daily portfolio summary report."""
        msg = (
            f"📊 *ATHENA Daily Performance Summary* 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Portfolio NAV*: `${nav:,.2f}`\n"
            f"• *Available Cash*: `${cash:,.2f}`\n"
            f"• *Trades Executed Today*: `{trades_count}`\n"
            f"• *Active Positions*: `{positions_count}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _Autonomous Hedge Fund Engine Active_"
        )
        await self.send_message(msg)


telegram_notifier = TelegramNotifier()
