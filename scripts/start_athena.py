"""
ATHENA Master Production Orchestrator
Coordinates the complete institutional schedule:
1. Immediate Morning Discovery Scan & Top Pick Execution (1 buy per day)
2. Every 2-Hour Holding Health & Progress Reports to Telegram
3. Afternoon Profit-Taking & Rebalance Session (1 sell/exit per day)
4. Daily 8:00 PM Comprehensive Market Intelligence Digest
Hard Invariants: Max 2 trades/day, >$200k buying power floor, Telegram notifications.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.common.config import settings
from scripts.daily_8pm_market_recap import generate_and_send_8pm_digest
from scripts.run_twice_daily_bot import run_afternoon_session, run_morning_session
from scripts.send_position_update import analyze_and_report_holdings
from services.notification_service.telegram_notifier import telegram_notifier


async def run_master_schedule():
    print("=" * 85)
    print("  🚀 ATHENA MASTER AUTONOMOUS HEDGE FUND ORCHESTRATOR IS LIVE")
    print("=" * 85)
    print("  • Schedule: Twice-Daily Trading (Morning Buy | Afternoon Profit-Take)")
    print("  • Health Checks: Every 2 Hours to Telegram (@AthenaAnalysis_bot)")
    print("  • Market Digest: Every Evening at 8:00 PM")
    print(f"  • Hard Margin Guard: Minimum ${settings.MIN_BUYING_POWER_RESERVE:,.2f} Buying Power Floor")
    print("  Press Ctrl + C anytime to pause.")
    print("=" * 85)

    # 0. Send startup notification to Telegram
    await telegram_notifier.send_message(
        "🚀 *ATHENA Master Trading System Started*\n\n"
        "• *Mode*: Twice-Daily Disciplined Swing Engine\n"
        "• *Trading Schedule*: Max 2 trades/day (1 Morning Buy, 1 Afternoon Exit)\n"
        "• *Intraday Updates*: Every 2 hours holding progress card\n"
        "• *Daily Recap*: 8:00 PM Market Intelligence Digest\n"
        "• *Safety Floor*: `$200,000.00 Minimum Buying Power Guaranteed`\n\n"
        "_Starting initial market scan now..._"
    )

    # 1. Run Initial Morning Session Immediately on Startup
    print("\n[Startup Action] Running Initial Market Discovery Scan...")
    await run_morning_session()

    # 2. Main Event Loop
    last_2hr_check = datetime.now()
    last_morning_run_date = datetime.now().date()
    last_afternoon_run_date = None
    last_8pm_run_date = None

    while True:
        now = datetime.now()

        # A. 2-Hour Position Progress Check (every 7200s)
        if (now - last_2hr_check).total_seconds() >= 7200:
            print(f"\n[{now.strftime('%H:%M:%S')}] Running 2-Hour Holding Progress Check...")
            await analyze_and_report_holdings()
            last_2hr_check = now

        # B. Morning Scan (Runs at 9:30 AM / morning on trading days)
        if now.hour == 9 and now.minute >= 30 and now.date() != last_morning_run_date:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering Morning Opening Session...")
            await run_morning_session()
            last_morning_run_date = now.date()

        # C. Afternoon Profit-Taking Session (Runs at 3:30 PM)
        if now.hour == 15 and now.minute >= 30 and now.date() != last_afternoon_run_date:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering Afternoon Profit-Taking Session...")
            await run_afternoon_session()
            last_afternoon_run_date = now.date()

        # D. Daily 8:00 PM Market Intelligence Digest
        if now.hour == 20 and now.date() != last_8pm_run_date:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering 8:00 PM Daily Market Intelligence Digest...")
            await generate_and_send_8pm_digest()
            last_8pm_run_date = now.date()

        # Heartbeat sleep
        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(run_master_schedule())
    except KeyboardInterrupt:
        print("\n[!] ATHENA Master Orchestrator safely paused by user.")
