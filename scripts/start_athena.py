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
from zoneinfo import ZoneInfo

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
from services.execution_service.alpaca_broker import alpaca_broker
from services.notification_service.telegram_notifier import telegram_notifier

US_EASTERN = ZoneInfo("America/New_York")

# (session number, ET hour, ET minute, name). Each fires once per day, within a 60-minute window.
SESSIONS = [
    (1, 9, 35, "Market Open Momentum Scan"),
    (2, 11, 30, "Mid-Morning Trend Continuation & Dip Buy"),
    (3, 13, 30, "Afternoon Sector Rotation & Institutional Flow"),
    (4, 15, 30, "Power Hour Profit-Taking & Swing Lock"),
]
SESSION_WINDOW_MINUTES = 60


async def market_is_open(now_et: datetime) -> bool:
    """Prefer Alpaca's market clock (handles holidays/early closes); fall back to ET weekday/hours."""
    clock = await alpaca_broker.is_market_open()
    if clock is not None:
        return clock
    if now_et.weekday() >= 5:
        return False
    minutes = now_et.hour * 60 + now_et.minute
    return 9 * 60 + 30 <= minutes < 16 * 60


async def safe_run(label: str, coro_fn, *args):
    """Run one scheduled job; a broker/network/data failure is logged and skipped, never fatal,
    and never replaced by fabricated account data."""
    try:
        await coro_fn(*args)
        return True
    except Exception as e:
        print(f"[!] {label} skipped: {type(e).__name__}: {e}")
        return False


async def run_master_schedule():
    print("=" * 85)
    print("  🚀 ATHENA MASTER AUTONOMOUS HEDGE FUND ORCHESTRATOR IS LIVE")
    print("=" * 85)
    print("  • Sessions (US Eastern, market-open only): 09:35 | 11:30 | 13:30 | 15:30")
    print("  • Health Checks: Every 2 Hours to Telegram (@AthenaAnalysis_bot)")
    print("  • Market Digest: Every Evening at 8:00 PM (local time)")
    print("  • Hard Risk Guard: Dynamic ATR Sizing & Portfolio Risk Management")
    print("  • Mode: PAPER trading only")
    print("  Press Ctrl + C anytime to pause.")
    print("=" * 85)

    await telegram_notifier.send_message(
        "🚀 *ATHENA Trading System Activated* (paper trading)\n\n"
        "• *Sessions (US Eastern)*: 09:35 | 11:30 | 13:30 | 15:30 — only while the market is open\n"
        "• *Position updates*: every 2 hours\n"
        "• *Daily report*: 8:00 PM local time\n"
        "• *Safety*: ATR sizing, risk veto, $200k buying-power floor"
    )

    last_2hr_check = datetime.now()
    executed_sessions = set()
    last_8pm_date = None

    # Startup scan: only if the market is open right now and we are inside a session window.
    now_et = datetime.now(US_EASTERN)
    if await market_is_open(now_et):
        print("\n[Startup Action] Market is open — running an initial scan session...")
        await safe_run("Startup session", run_trading_session, 1, SESSIONS[0][3])
        executed_sessions.add((now_et.date(), 1))
    else:
        print(f"\n[Startup] US market closed (ET {now_et.strftime('%a %H:%M')}). Waiting for the next session window.")

    while True:
        now = datetime.now()
        now_et = datetime.now(US_EASTERN)
        today_et = now_et.date()

        # A. 2-Hour Position Progress Check
        if (now - last_2hr_check).total_seconds() >= 7200:
            print(f"\n[{now.strftime('%H:%M:%S')}] Running 2-Hour Holding Progress Check...")
            await safe_run("Position update", analyze_and_report_holdings)
            last_2hr_check = now

        # B. Trading sessions in US Eastern time, market-open only
        minutes_et = now_et.hour * 60 + now_et.minute
        for num, hh, mm, name in SESSIONS:
            start = hh * 60 + mm
            if (
                start <= minutes_et < start + SESSION_WINDOW_MINUTES
                and (today_et, num) not in executed_sessions
            ):
                executed_sessions.add((today_et, num))  # mark first: never retry-spam a failing session
                if await market_is_open(now_et):
                    print(f"\n[ET {now_et.strftime('%H:%M')}] Triggering Session {num}: {name}...")
                    await safe_run(f"Session {num}", run_trading_session, num, name)
                else:
                    print(f"\n[ET {now_et.strftime('%H:%M')}] Session {num} skipped: market closed.")
                break

        # C. Daily 8:00 PM digest (local time)
        if now.hour == 20 and now.date() != last_8pm_date:
            print(f"\n[{now.strftime('%H:%M:%S')}] Triggering 8:00 PM Daily Report...")
            await safe_run("Daily report", generate_and_send_8pm_digest)
            last_8pm_date = now.date()

        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(run_master_schedule())
    except KeyboardInterrupt:
        print("\n[!] ATHENA Master Orchestrator safely paused by user.")
