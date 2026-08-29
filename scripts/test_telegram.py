"""
ATHENA Telegram Bot Connection & Test Script
Verifies Telegram credentials and sends a test alert.
"""

import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.common.config import settings
from services.notification_service.telegram_notifier import telegram_notifier


async def test_telegram():
    print("=" * 75)
    print("  ATHENA TELEGRAM BOT NOTIFICATION TEST")
    print("=" * 75)

    if not telegram_notifier.is_configured():
        print("\n[!] Telegram Bot is not configured yet in `.env`.")
        print("    To set it up:")
        print("    1. Open Telegram and search for `@BotFather`")
        print("    2. Type `/newbot` to create your bot and copy your API Token")
        print("    3. Start a chat with your bot and send any message (e.g. 'hello')")
        print("    4. Search for `@userinfobot` to get your Telegram User/Chat ID")
        print("    5. Add them to your `Athena/.env` file:")
        print("       TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("       TELEGRAM_CHAT_ID=your_chat_id_here")
        print("\n" + "=" * 75)
        return

    print(f"\n[+] Testing connection to Telegram Chat ID: {settings.TELEGRAM_CHAT_ID}...")
    success = await telegram_notifier.send_message(
        "🤖 *ATHENA Multi-Agent Quantitative OS*\n\n"
        "✅ *Telegram Integration Successful!*\n"
        "You will now receive instant notifications whenever the AI agents place or fill a trade.\n\n"
        "👉 _Ready to trade on Alpaca Paper API_"
    )

    if success:
        print("[OK] SUCCESS! Test message sent to your Telegram. Check your phone/app!")
    else:
        print("[X] Failed to send message. Please verify your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")

    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(test_telegram())
