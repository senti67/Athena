"""
ATHENA Continuous Autonomous Trading Daemon for Alpaca Paper API
Scans the universe periodically, runs 14 AI agents and 16 strategies,
debates, risk-checks, and executes orders automatically to your Alpaca account.
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

from scripts.run_alpaca_live import run_alpaca_pipeline

UNIVERSE = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "SPY"]


async def main(interval_seconds: int = 60):
    print("=" * 85)
    print("  ATHENA CONTINUOUS AUTONOMOUS ALPACA TRADING DAEMON")
    print(f"  Scanning Universe: {', '.join(UNIVERSE)}")
    print(f"  Cycle Interval: Every {interval_seconds} seconds (Press Ctrl+C to stop)")
    print("=" * 85)

    cycle = 1
    while True:
        print(f"\n>>> [CYCLE #{cycle}] Starting Autonomous Market Scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} <<<")
        for symbol in UNIVERSE:
            try:
                print(f"\n--- Analyzing & Evaluating {symbol} ---")
                await run_alpaca_pipeline(symbol)
                await asyncio.sleep(2)  # Brief rate-limit buffer
            except Exception as e:
                print(f"[!] Error processing {symbol}: {e}")

        print(f"\n>>> [CYCLE #{cycle} COMPLETE] Sleeping for {interval_seconds}s until next scan... <<<")
        cycle += 1
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    try:
        asyncio.run(main(interval))
    except KeyboardInterrupt:
        print("\n[!] ATHENA Autonomous Daemon stopped by user.")
