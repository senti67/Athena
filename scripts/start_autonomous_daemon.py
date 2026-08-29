"""
ATHENA 24/7 Master Autonomous Trading Daemon
Continuously runs 14 AI agents, 16 quantitative strategies, debate engine,
risk management, Alpaca paper trade execution, and instant Telegram alerts.
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
from scripts.run_alpaca_live import run_alpaca_pipeline
from services.notification_service.telegram_notifier import telegram_notifier
from services.portfolio_service.optimizer import portfolio_manager

# Comprehensive Global & Indian Universe
UNIVERSE = [
    "NVDA",
    "AAPL",
    "MSFT",
    "TSLA",
    "GOOGL",
    "AMZN",
    "META",
    "SPY",
    "RKLB",
    "ICICIBANK",
    "HDFCBANK",
    "BHARTIARTL",
    "RELIANCE",
    "TCS",
]


async def run_24_7_daemon(interval_seconds: int = 120):
    print("=" * 85)
    print("  🚀 ATHENA 24/7 MULTI-AGENT AUTONOMOUS HEDGE FUND DAEMON")
    print(f"  Watching Universe: {', '.join(UNIVERSE)}")
    print(f"  Scan Frequency: Every {interval_seconds} seconds")
    print(f"  Target Broker: Alpaca Paper API ({settings.ALPACA_BASE_URL})")
    print(f"  Telegram Alerts: Active (@AthenaAnalysis_bot)")
    print("  Press Ctrl + C anytime to pause.")
    print("=" * 85)

    # Send startup alert to Telegram
    await telegram_notifier.send_message(
        "🚀 *ATHENA 24/7 Autonomous Daemon Started*\n\n"
        f"• *Monitoring*: `{len(UNIVERSE)} Assets` (US Tech, Space & Indian Bluechips)\n"
        f"• *Scan Frequency*: Every `{interval_seconds}s`\n"
        f"• *AI Agents*: `14 Active` | *Quant Strategies*: `16 Active`\n"
        f"• *Execution*: `Alpaca Paper Trading`\n\n"
        "_Autonomous hedge fund operating system is live and monitoring markets._"
    )

    cycle = 1
    while True:
        cycle_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*30} [CYCLE #{cycle} - {cycle_start}] {'='*30}")

        trades_in_cycle = 0
        for symbol in UNIVERSE:
            try:
                print(f"\n--- Scanning Asset: {symbol} ---")
                await run_alpaca_pipeline(symbol)
                trades_in_cycle += 1
                await asyncio.sleep(2)  # 2s rate limit cushion
            except Exception as e:
                print(f"[!] Error processing {symbol}: {e}")

        # Cycle summary
        port = portfolio_manager.get_portfolio_state()
        print(f"\n[Cycle #{cycle} Complete] Portfolio NAV: ${port.nav:,.2f} | Open Positions: {len(port.positions)}")
        print(f"Sleeping for {interval_seconds} seconds until next autonomous market scan...\n")

        cycle += 1
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    # Custom interval (default: 120 seconds = 2 minutes)
    freq = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    try:
        asyncio.run(run_24_7_daemon(interval_seconds=freq))
    except KeyboardInterrupt:
        print("\n[!] ATHENA 24/7 Daemon safely paused by user.")
