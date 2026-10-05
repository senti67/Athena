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
from services.notification_service.trade_card import DailyReportCard
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector

# Key Macro & Sector Benchmarks
MACRO_BENCHMARKS = [
    {"name": "S&P 500", "symbol": "SPY", "category": "US Equities"},
    {"name": "Nasdaq 100", "symbol": "QQQ", "category": "US Equities"},
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

    # 4. Construct DailyReportCard from MEASURED values only (None -> "N/A" in the message)
    today_date = datetime.now().strftime("%Y-%m-%d")

    def _f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    # Daily P&L from Alpaca's own prior-close equity
    last_equity = _f(acct.get("last_equity"))
    daily_val = (live_nav - last_equity) if last_equity else None
    daily_pct = (daily_val / last_equity * 100) if (daily_val is not None and last_equity) else None

    # Exposure / largest position from real position market values
    mvs = {p.get("symbol", "?"): abs(_f(p.get("market_value")) or 0.0) for p in open_positions}
    exposure_pct = (sum(mvs.values()) / live_nav * 100) if (live_nav > 0) else None
    if mvs and live_nav > 0:
        big_sym = max(mvs, key=mvs.get)
        largest_pos = f"{big_sym} · {mvs[big_sym] / live_nav * 100:.1f}%"
    else:
        largest_pos = "No open positions" if live_nav > 0 else None

    def _regime_label(symbol):
        for m in macro_summaries:
            if m["symbol"] == symbol:
                v = m["regime"]
                icon = "🟢" if "BULL" in v else ("🔴" if "BEAR" in v else "🟡")
                return f"{icon} {v.replace('_', ' ')}"
        return None

    daily_card = DailyReportCard(
        date_str=today_date,
        portfolio_value=live_nav,
        daily_pnl_pct=daily_pct,
        daily_pnl_val=daily_val,
        portfolio_exposure_pct=exposure_pct,
        largest_position_str=largest_pos,
        spy_regime=_regime_label("SPY"),
        qqq_regime=_regime_label("QQQ"),
        timestamp=datetime.utcnow(),
    )

    # 5. Send to Telegram
    success = await telegram_notifier.send_daily_report(daily_card)
    if success:
        print("\n[OK] 8:00 PM Daily Market Intelligence delivered successfully to your Telegram!")
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
