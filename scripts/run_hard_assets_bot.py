"""
ATHENA Macro & Hard Assets Autonomous Trading Bot (Bitcoin, Gold & Silver)
Monitors Bitcoin (BTC/USD & IBIT), Physical Gold (GLD), and Physical Silver (SLV).
Strict swing-trading discipline, zero continuous churn, and $200k buying power protection.
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
from services.execution_service.alpaca_broker import alpaca_broker
from services.notification_service.telegram_notifier import telegram_notifier
from services.portfolio_service.optimizer import portfolio_manager

# Focused Universe: Bitcoin & Precious Metals
HARD_ASSETS_UNIVERSE = [
    {"name": "Bitcoin", "symbol": "IBIT", "alt_symbol": "BTCUSD"},
    {"name": "Gold", "symbol": "GLD", "alt_symbol": "IAU"},
    {"name": "Silver", "symbol": "SLV", "alt_symbol": "PSLV"},
]


async def run_hard_assets_cycle():
    print("\n" + "=" * 80)
    print("  🏆 ATHENA MACRO & HARD ASSETS ENGINE (BITCOIN | GOLD | SILVER)")
    print(f"  Target Broker: Alpaca Paper API ({settings.ALPACA_BASE_URL})")
    print(f"  Minimum Buying Power Floor: ${settings.MIN_BUYING_POWER_RESERVE:,.2f}")
    print("=" * 80)

    # 1. Fetch current Alpaca state
    acct = await alpaca_broker.get_account()
    open_positions = await alpaca_broker.get_positions()
    open_orders = await alpaca_broker.get_open_orders()
    portfolio_manager.sync_from_alpaca(acct, open_positions)

    live_bp = float(acct.get("buying_power", 0.0))
    live_cash = float(acct.get("cash", 0.0))
    print(f"\n[Account Sync] Cash: ${live_cash:,.2f} | Buying Power: ${live_bp:,.2f} | Active Positions: {len(open_positions)}")

    # 2. Check hard Buying Power Floor
    if live_bp <= settings.MIN_BUYING_POWER_RESERVE:
        print(f"\n[RISK VETO] Buying power (${live_bp:,.2f}) is at or below $200k minimum reserve floor.")
        print("             No new hard asset purchases will be evaluated.")
        return

    # 3. Analyze each Hard Asset with 14 AI Agents & Quant Models
    held_symbols = [p.get("symbol", "").upper() for p in open_positions]
    queued_symbols = [o.get("symbol", "").upper() for o in open_orders]

    for asset in HARD_ASSETS_UNIVERSE:
        sym = asset["symbol"]
        name = asset["name"]
        print(f"\n>>> Evaluating Macro Opportunity: {name} ({sym}) <<<")

        # Anti-Churn Check: Do not buy if already held
        if sym in held_symbols or sym in queued_symbols:
            print(f"[HOLD] {name} ({sym}) is already held in your portfolio / active order book.")
            print(f"       Patiently holding for target expansion. (Zero continuous churn)")
            continue

        try:
            await run_alpaca_pipeline(sym)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[!] Error analyzing {name} ({sym}): {e}")

    print("\n" + "=" * 80)
    print("  [OK] Hard Assets Scan Cycle Completed. Waiting for next market interval...")
    print("=" * 80)


async def main():
    # Notify Telegram of Hard Asset Focus Mode
    await telegram_notifier.send_message(
        "🏆 *ATHENA Macro & Hard Assets Mode Activated*\n\n"
        "• *Target Assets*: `Bitcoin (IBIT)`, `Gold (GLD)`, `Silver (SLV)`\n"
        "• *Strategy*: Macro Trend & Monetary Inflation Hedge\n"
        "• *Discipline*: Strict anti-churn (max 1 position per asset)\n"
        "• *Floor Protected*: `$200,000.00 Minimum Buying Power`\n\n"
        "_Continuous stock buying stopped. System is now purely monitoring Bitcoin & Precious Metals._"
    )

    # Run single cycle or periodic scan
    await run_hard_assets_cycle()


if __name__ == "__main__":
    asyncio.run(main())
