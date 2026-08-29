"""
ATHENA 2-Hour Holding Health & Progress Analysis Reporter
Analyzes all currently held positions every 2 hours and sends a detailed progress card to Telegram.
"""

import argparse
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
from services.data_service.pipeline import data_pipeline
from services.execution_service.alpaca_broker import alpaca_broker
from services.feature_service.pipeline import feature_pipeline
from services.notification_service.telegram_notifier import telegram_notifier
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector


async def analyze_and_report_holdings():
    print("\n" + "=" * 80)
    print("  📊 ATHENA 2-HOUR HOLDING HEALTH & PROGRESS ANALYSIS")
    print(f"  Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    acct = await alpaca_broker.get_account()
    open_positions = await alpaca_broker.get_positions()
    portfolio_manager.sync_from_alpaca(acct, open_positions)

    live_bp = float(acct.get("buying_power", 400000.0))
    live_cash = float(acct.get("cash", 100000.0))
    live_nav = float(acct.get("equity", 100000.0))

    print(f"[Account Status] NAV: ${live_nav:,.2f} | Cash: ${live_cash:,.2f} | Buying Power: ${live_bp:,.2f}")
    print(f"[Active Positions]: {len(open_positions)}")

    if len(open_positions) == 0:
        print("\n[OK] No active positions held right now. Portfolio is 100% in cash.")
        await telegram_notifier.send_message(
            "📊 *ATHENA 2-Hour Portfolio Status*\n\n"
            "• *Status*: 🛡️ *100% Cash Buffer Active*\n"
            f"• *Available Cash*: `${live_cash:,.2f}`\n"
            f"• *Buying Power*: `${live_bp:,.2f}` (Guaranteed >$200k Floor)\n"
            "• *Active Holdings*: `0 Positions`\n\n"
            "_Next stock selection will occur at the next scheduled Morning Open session._"
        )
        print("=" * 80)
        return

    for pos in open_positions:
        sym = pos.get("symbol", "").upper()
        shares = float(pos.get("qty", 0))
        entry_px = float(pos.get("avg_entry_price", 0))
        cur_px = float(pos.get("current_price", entry_px))
        unrealized = float(pos.get("unrealized_pl", 0))
        unrealized_pct = float(pos.get("unrealized_plpc", 0)) * 100

        print(f"\nAnalyzing Active Holding: {sym} ({shares:.0f} shares)...")
        try:
            candles = await data_pipeline.ingest_candles(sym, limit=100)
            features = feature_pipeline.compute_features(sym, candles)
            regime = regime_detector.detect_regime(features)
            rsi = features.technical.rsi_14
            atr = features.technical.atr_14 or (cur_px * 0.015)

            stop_loss = round(max(cur_px - (2.0 * atr), features.technical.pivot_support * 0.99), 2)
            take_profit = round(cur_px + (4.0 * atr), 2)

            # Quantitative AI Health Verdict
            if unrealized_pct >= 3.0:
                verdict = "PROFIT EXPANSION (Near Target)"
            elif unrealized_pct >= 0.5:
                verdict = "HEALTHY BULLISH EXPANSION"
            elif unrealized_pct >= -1.0:
                verdict = "NORMAL INTRADAY CONSOLIDATION"
            else:
                verdict = "CAUTION: MONITORING STOP-LOSS BUFFER"

            print(f"  • Entry: ${entry_px:,.2f} -> Current: ${cur_px:,.2f} | P&L: {unrealized_pct:+.2f}%")
            print(f"  • RSI(14): {rsi:.1f} | Regime: {regime.regime.value} | Verdict: {verdict}")
            print(f"  • Take-Profit Target: ${take_profit:,.2f} | Stop-Loss: ${stop_loss:,.2f}")

            # Send rich Telegram Health Card
            await telegram_notifier.notify_position_health_report(
                symbol=sym,
                shares=shares,
                entry_price=entry_px,
                current_price=cur_px,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=unrealized_pct,
                rsi=rsi,
                regime=regime.regime.value,
                verdict=verdict,
                stop_loss=stop_loss,
                take_profit=take_profit,
                nav=live_nav,
                buying_power=live_bp,
            )
            print(f"[OK] 2-Hour Progress Card sent to Telegram for {sym}!")
        except Exception as e:
            print(f"[!] Error analyzing {sym}: {e}")

    print("\n" + "=" * 80)


async def main():
    parser = argparse.ArgumentParser(description="ATHENA 2-Hour Holding Progress Reporter")
    parser.add_argument(
        "--daemon",
        type=int,
        default=0,
        help="Run continuously in background with interval in seconds (e.g. 7200 for every 2 hours)",
    )
    args = parser.parse_args()

    if args.daemon > 0:
        print(f"🚀 Starting 2-Hour Progress Daemon (Interval: {args.daemon} seconds)...")
        while True:
            await analyze_and_report_holdings()
            print(f"\nSleeping for {args.daemon // 60} minutes until next progress report...\n")
            await asyncio.sleep(args.daemon)
    else:
        # Run once immediately
        await analyze_and_report_holdings()


if __name__ == "__main__":
    asyncio.run(main())
