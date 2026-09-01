"""
ATHENA Master Production Orchestrator (4-Times-Daily Execution Schedule)
Coordinates the complete institutional trading schedule:
1. Four Tactical Trading Sessions:
   - Session 1: 09:30 AM EST (Market Open Momentum Scan & Buy)
   - Session 2: 11:30 AM EST (Mid-Morning Trend Continuation & Dip Buy)
   - Session 3: 01:30 PM EST (Afternoon Sector Rotation & Institutional Flow)
   - Session 4: 03:30 PM EST (Power Hour Profit-Taking & Swing Lock)
2. Every 2-Hour Holding Health & Progress Reports to Telegram
3. Daily 8:00 PM Comprehensive Market Intelligence Digest
Hard Invariants: Max 4 buys/day, >$200k buying power floor, Telegram notifications.
"""

import asyncio
import os
import sys
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.common.config import settings
from scripts.daily_8pm_market_recap import generate_and_send_8pm_digest
from scripts.run_four_times_daily_bot import run_trading_session
from scripts.send_position_update import analyze_and_report_holdings
from services.notification_service.telegram_notifier import telegram_notifier


async def run_master_schedule():
    print("=" * 85)
    print("  🚀 ATHENA MASTER AUTONOMOUS HEDGE FUND ORCHESTRATOR IS LIVE")
    print("=" * 85)
    print("  • Schedule: 4 Times Per Day (Open | Mid-Morning | Afternoon | Power Hour)")
    print("  • Health Checks: Every 2 Hours to Telegram (@AthenaAnalysis_bot)")
    print("  • Market Digest: Every Evening at 8:00 PM")
    print(f"  • Hard Margin Guard: Minimum ${settings.MIN_BUYING_POWER_RESERVE:,.2f} Buying Power Floor")
    print("  Press Ctrl + C anytime to pause.")
    print("=" * 85)

    # 0. Send startup notification to Telegram
    await telegram_notifier.send_message(
        "🚀 *ATHENA 4-Times-Daily Trading System Activated*\n\n"
        "• *Frequency*: `4 Execution Sessions per Day`\n"
        "• *Sessions*: Open (9:30 AM) | Mid-Morning (11:30 AM) | Afternoon (1:30 PM) | Close (3:30 PM)\n"
        "• *Profit Taking*: Automatic on +3.0%+ gain expansion\n"
        "• *Intraday Updates*: Every 2 hours holding progress card\n"
        "• *Daily Recap*: 8:00 PM Market Intelligence Digest\n"
        "• *Safety Floor*: `$200,000.00 Minimum Buying Power Guaranteed`\n\n"
        "_Starting initial tactical scan now..._"
    )

    # 1. Run Session 1 immediately on startup
    print("\n[Startup Action] Running Initial Tactical Trading Session...")
    await run_trading_session(1, "Market Open Momentum Scan")

    # 2. Main Scheduled Event Loop
    last_2hr_check = datetime.now()
    executed_sessions = set()
    last_8pm_date = None

    while True:
        now = datetime.now()
        today = now.date()

        # A. 2-Hour Position Progress Check (every 7200s)
        if (now - last_2hr_check).total_seconds() >= 7200:
            print(f"\n[{now.strftime('%H:%M:%S')}] Running 2-Hour Holding Progress Check...")
            await analyze_and_report_holdings()
            last_2hr_check = now

        # B. 4 Daily Trading Sessions (Mapped to Market Hours / Intervals)
        # Session 1: 09:30 - 10:30 (Market Open)
        if now.hour == 9 and (today, 1) not in executed_sessions:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering Session 1: Market Open Momentum Scan...")
            await run_trading_session(1, "Market Open Momentum Scan")
            executed_sessions.add((today, 1))

        # Session 2: 11:30 - 12:30 (Mid-Morning)
        elif now.hour == 11 and (today, 2) not in executed_sessions:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering Session 2: Mid-Morning Trend & Dip Buy...")
            await run_trading_session(2, "Mid-Morning Trend Continuation & Dip Buy")
            executed_sessions.add((today, 2))

        # Session 3: 13:30 - 14:30 (Afternoon Sector Rotation)
        elif now.hour == 13 and (today, 3) not in executed_sessions:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering Session 3: Afternoon Sector Rotation...")
            await run_trading_session(3, "Afternoon Sector Rotation & Institutional Flow")
            executed_sessions.add((today, 3))

        # Session 4: 15:30 - 16:00 (Power Hour & Close Rebalance)
        elif now.hour == 15 and (today, 4) not in executed_sessions:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering Session 4: Power Hour Profit-Taking & Swing Lock...")
            await run_trading_session(4, "Power Hour Profit-Taking & Swing Lock")
            executed_sessions.add((today, 4))

        # C. Daily 8:00 PM Market Intelligence Digest
        if now.hour == 20 and today != last_8pm_date:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering 8:00 PM Daily Market Intelligence Digest...")
            await generate_and_send_8pm_digest()
            last_8pm_date = today

        # Sleep heartbeat
        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(run_master_schedule())
    except KeyboardInterrupt:
        print("\n[!] ATHENA Master Orchestrator safely paused by user.")
