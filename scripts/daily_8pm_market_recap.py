"""
ATHENA Daily 8:00 PM Comprehensive Market Intelligence & Performance Digest
Delivers a macro recap of US Equities, Indian Equities, Bitcoin, Gold, Silver,
and ATHENA's daily portfolio P&L directly to Telegram every evening at 8:00 PM.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, time, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.common.config import settings
from services.data_service.pipeline import data_pipeline
from services.execution_service.alpaca_broker import alpaca_broker
from services.feature_service.pipeline import feature_pipeline
from services.notification_service.telegram_notifier import telegram_notifier
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector

# Key Macro & Sector Benchmarks
MACRO_BENCHMARKS = [
    {"name": "S&P 500", "symbol": "SPY", "category": "US Equities"},
    {"name": "Bitcoin ETF", "symbol": "IBIT", "category": "Crypto"},
    {"name": "Physical Gold", "symbol": "GLD", "category": "Commodities"},
    {"name": "Physical Silver", "symbol": "SLV", "category": "Precious Metals"},
    {"name": "India MSCI ETF", "symbol": "INDA", "category": "Indian Market"},
    {"name": "Nvidia (AI Lead)", "symbol": "NVDA", "category": "Tech Leaders"},
]


async def generate_and_send_8pm_digest():
    print("\n" + "=" * 85)
    print("  🌙 ATHENA DAILY 8:00 PM MARKET INTELLIGENCE & PERFORMANCE DIGEST")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Generated at: {now_str}")
    print("=" * 85)

    # 1. Fetch live portfolio & Alpaca status
    acct = await alpaca_broker.get_account()
    open_positions = await alpaca_broker.get_positions()
    portfolio_manager.sync_from_alpaca(acct, open_positions)

    live_nav = float(acct.get("equity", 100000.0))
    live_cash = float(acct.get("cash", 100000.0))
    live_bp = float(acct.get("buying_power", 400000.0))

    # 2. Ingest & Analyze Macro Benchmarks
    macro_summaries = []
    print("\nScanning Macro Benchmarks & Market Regimes...")
    for item in MACRO_BENCHMARKS:
        sym = item["symbol"]
        name = item["name"]
        try:
            candles = await data_pipeline.ingest_candles(sym, limit=60)
            if len(candles) >= 2:
                latest = candles[-1].close
                prev = candles[-2].close
                pct_change = ((latest - prev) / prev) * 100
                features = feature_pipeline.compute_features(sym, candles)
                regime = regime_detector.detect_regime(features)

                macro_summaries.append({
                    "name": name,
                    "symbol": sym,
                    "price": latest,
                    "change_pct": pct_change,
                    "rsi": features.technical.rsi_14,
                    "regime": regime.regime.value,
                })
                print(f"  • {name:<18} ({sym}): ${latest:>8.2f} | {pct_change:>+6.2f}% | RSI: {features.technical.rsi_14:>4.1f} | {regime.regime.value}")
        except Exception as e:
            print(f"  • {name} ({sym}): Error fetching data ({e})")

    # 3. Format Holding Progress Summary
    holdings_text = ""
    if len(open_positions) > 0:
        for pos in open_positions:
            s = pos.get("symbol")
            q = float(pos.get("qty", 0))
            entry = float(pos.get("avg_entry_price", 0))
            cur = float(pos.get("current_price", entry))
            pnl_pct = float(pos.get("unrealized_plpc", 0)) * 100
            pnl_val = float(pos.get("unrealized_pl", 0))
            emoji = "🟢" if pnl_pct >= 0 else "🔴"
            holdings_text += f"• `{s}` ({q:.0f} sh): {emoji} *{pnl_pct:+.2f}%* (`${pnl_val:+,.2f}`) @ ${cur:,.2f}\n"
    else:
        holdings_text = "• `100% Cash / Dry Powder` (Ready for tomorrow's morning scan)\n"

    # 4. Construct Rich Telegram 8:00 PM Digest Card
    today_date = datetime.now().strftime("%A, %B %d, %Y")

    report = (
        f"🌙 *ATHENA 8:00 PM DAILY MARKET INTELLIGENCE* 🌙\n"
        f"📅 _{today_date}_\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 *Macro & Hard Asset Closes*:\n"
    )

    for m in macro_summaries:
        chg_emoji = "🟢" if m["change_pct"] >= 0 else "🔴"
        report += (
            f"• *{m['name']}* (`{m['symbol']}`): `${m['price']:,.2f}` | "
            f"{chg_emoji} *{m['change_pct']:+.2f}%* (RSI: `{m['rsi']:.0f}`)\n"
        )

    report += (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💼 *ATHENA Portfolio Evening Status*:\n"
        f"• *Portfolio NAV*: `${live_nav:,.2f}`\n"
        f"• *Available Cash*: `${live_cash:,.2f}`\n"
        f"• *Buying Power*: `${live_bp:,.2f}` (Floor Protected $\\ge\\$200\\text{{k}}$)\n"
        f"• *Active Holdings*:\n{holdings_text}"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔭 *Tomorrow's Outlook & Strategy*:\n"
        f"• AI Agents will scan the opening bell for the #1 highest-conviction setup at **9:30 AM EST**.\n"
        f"• Strict discipline: Max 1 morning entry, afternoon profit-taking.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _ATHENA Multi-Agent Quantitative OS_"
    )

    # 5. Send to Telegram
    success = await telegram_notifier.send_message(report)
    if success:
        print("\n[OK] 8:00 PM Daily Market Digest delivered successfully to your Telegram!")
    else:
        print("\n[!] Could not send Telegram message. Please check token/chat_id.")

    print("=" * 85)


async def schedule_daily_8pm():
    """Waits and triggers the 8:00 PM digest every evening automatically."""
    print("🚀 ATHENA 8:00 PM Daily Digest Scheduler Started.")
    print("Will automatically fire every day at 8:00 PM (20:00 local time). Press Ctrl + C to pause.")

    while True:
        now = datetime.now()
        target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)

        # If 8:00 PM has already passed today, target tomorrow 8:00 PM
        if now >= target_time:
            target_time += timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()
        hours = int(wait_seconds // 3600)
        minutes = int((wait_seconds % 3600) // 60)
        print(f"\n[Scheduler] Next 8:00 PM Daily Digest in {hours}h {minutes}m ({target_time.strftime('%Y-%m-%d 20:00')}). Waiting...")

        await asyncio.sleep(wait_seconds)
        print("\n⏰ It's 8:00 PM! Generating daily market intelligence digest...")
        await generate_and_send_8pm_digest()
        await asyncio.sleep(60)  # Sleep 1 min to prevent duplicate trigger


async def main():
    parser = argparse.ArgumentParser(description="ATHENA 8:00 PM Daily Market Intelligence Digest")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run continuously and trigger automatically every day at 8:00 PM",
    )
    args = parser.parse_args()

    if args.schedule:
        await schedule_daily_8pm()
    else:
        # Run immediately
        await generate_and_send_8pm_digest()


if __name__ == "__main__":
    asyncio.run(main())
