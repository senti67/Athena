"""
ATHENA Real-Time Multi-Channel Notification Service
Sends instant trade notifications via:
1. Windows Desktop Toast Notifications & System Audio Chime
2. Telegram Bot Notifications
3. Discord Rich Webhooks
4. Slack Webhooks
"""

import asyncio
import os
import subprocess
import sys
from typing import Optional
import httpx

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from packages.common.config import settings
from packages.event_bus.bus import event_bus
from packages.logging.logger import get_logger
from packages.schemas.events import Event, EventType

logger = get_logger("athena.notification_service")


class NotificationService:
    """Multi-channel notification dispatcher for autonomous agent orders and risk events."""

    def __init__(self):
        self.telegram_token = settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = settings.TELEGRAM_CHAT_ID
        self.discord_webhook = settings.DISCORD_WEBHOOK_URL
        self.slack_webhook = settings.SLACK_WEBHOOK_URL
        self.desktop_enabled = settings.DESKTOP_NOTIFICATIONS_ENABLED
        self.audio_enabled = settings.AUDIO_ALERTS_ENABLED

    def play_chime(self):
        """Plays Windows system notification sound."""
        if HAS_WINSOUND and self.audio_enabled:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    def send_windows_toast(self, title: str, message: str):
        """Displays native Windows desktop notification toast."""
        if not self.desktop_enabled or sys.platform != "win32":
            return

        try:
            # Escape strings for PowerShell
            clean_title = title.replace('"', '`"')
            clean_msg = message.replace('"', '`"').replace("\n", " ")

            ps_script = f"""
            [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.Visible = $True
            $notify.ShowBalloonTip(10000, "{clean_title}", "{clean_msg}", [System.Windows.Forms.ToolTipIcon]::Info)
            """
            subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.play_chime()
        except Exception as e:
            logger.debug(f"Desktop notification error: {e}")

    async def send_telegram(self, text: str):
        """Sends rich Markdown message to Telegram chat."""
        if not (self.telegram_token and self.telegram_chat_id):
            return

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                logger.warning(f"Telegram notification failed: {e}")

    async def send_discord(self, title: str, description: str, color: int = 0x00FF00, fields: Optional[list] = None):
        """Sends rich embed card to Discord channel."""
        if not self.discord_webhook:
            return

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "footer": {"text": "ATHENA Multi-Agent Quantitative OS"},
        }
        if fields:
            embed["fields"] = fields

        payload = {"embeds": [embed]}
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                await client.post(self.discord_webhook, json=payload)
            except Exception as e:
                logger.warning(f"Discord notification failed: {e}")

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
    ):
        """Dispatches multi-channel notification for a new autonomous order."""
        title = f"🚀 ATHENA Trade: {action} {quantity:.0f} {symbol}"
        summary = (
            f"Executed: {action} {quantity:.0f} {symbol} @ ~${price:,.2f}\n"
            f"Confidence: {confidence*100:.0f}%\n"
            f"Target: ${take_profit:,.2f} | Stop Loss: ${stop_loss:,.2f}"
            if (take_profit and stop_loss)
            else f"Executed: {action} {quantity:.0f} {symbol} @ ~${price:,.2f}"
        )

        # 1. Desktop Notification
        self.send_windows_toast(title, summary)

        # 2. Telegram Notification
        tg_text = (
            f"🤖 *ATHENA Autonomous Trade Alert*\n\n"
            f"• *Asset*: `{symbol}`\n"
            f"• *Action*: *{action}*\n"
            f"• *Quantity*: `{quantity:.0f}` shares\n"
            f"• *Price*: `${price:,.2f}`\n"
            f"• *Confidence*: `{confidence*100:.0f}%`\n"
            f"• *Order ID*: `{order_id}`\n"
        )
        if stop_loss and take_profit:
            tg_text += f"• *Stop Loss*: `${stop_loss:,.2f}`\n• *Take Profit*: `${take_profit:,.2f}`\n"
        tg_text += "\n_Live on Alpaca Paper Dashboard_"

        asyncio.create_task(self.send_telegram(tg_text))

        # 3. Discord Embed Notification
        color = 0x00FF00 if action.upper() == "BUY" else 0xFF0000
        discord_fields = [
            {"name": "Symbol", "value": symbol, "inline": True},
            {"name": "Action", "value": action, "inline": True},
            {"name": "Quantity", "value": f"{quantity:.0f}", "inline": True},
            {"name": "Estimated Price", "value": f"${price:,.2f}", "inline": True},
            {"name": "Confidence", "value": f"{confidence*100:.0f}%", "inline": True},
            {"name": "Order ID", "value": f"`{order_id}`", "inline": False},
        ]
        asyncio.create_task(self.send_discord(title, summary, color=color, fields=discord_fields))

    async def notify_risk_veto(self, symbol: str, reason: str):
        """Notifies when risk veto triggers."""
        title = f"🛡️ ATHENA Risk VETO: {symbol}"
        msg = f"Order blocked by Risk Management: {reason}"
        self.send_windows_toast(title, msg)


notification_service = NotificationService()
