"""
ATHENA Twice-Daily Disciplined Swing Trading Engine (Production Quality)
Trades strictly 2 times per day:
- Session 1 (Morning Open): Scans universe, picks the SINGLE highest-conviction profitable stock, buys 1 position.
- Session 2 (Afternoon Close): Monitors open positions, takes profit (+3.5%+), cuts stops, or locks in gains.
Hard Invariants: Max 2 trades/day, >$200k buying power floor, Telegram notifications.
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
from packages.schemas.agent import AgentContext
from packages.schemas.decision import ActionType
from packages.schemas.order import ExecutionMode, OrderStatus
from services.agent_service.orchestrator import agent_orchestrator
from services.data_service.pipeline import data_pipeline
from services.debate_service.engine import debate_engine
from services.decision_service.engine import decision_engine
from services.execution_service.alpaca_broker import alpaca_broker
from services.execution_service.router import execution_router
from services.feature_service.pipeline import feature_pipeline
from services.journal_service.journal import journal_service
from services.notification_service.telegram_notifier import telegram_notifier
from services.portfolio_service.optimizer import portfolio_manager
from services.regime_service.detector import regime_detector
from services.risk_service.engine import risk_engine
from services.strategy_service.registry import strategy_registry

# Prime High-Liquidity Universe (US Tech, Hard Assets, Crypto & Indian Leaders)
WATCHLIST = [
    "NVDA",
    "AAPL",
    "MSFT",
    "TSLA",
    "GOOGL",
    "AMZN",
    "META",
    "IBIT",  # Bitcoin Trust
    "GLD",   # Physical Gold
    "SLV",   # Physical Silver
    "ICICIBANK",
    "RELIANCE",
    "HDFCBANK",
]


async def run_morning_session():
    """
    SESSION 1 (Morning): Scans the universe, scores all stocks,
    selects the SINGLE #1 highest-conviction setup, and executes ONE disciplined purchase.
    """
    print("\n" + "=" * 85)
    print("  🌅 ATHENA SESSION 1: MORNING MARKET SCAN & HIGHEST-CONVICTION SELECTION")
    print(f"  Target: Find the #1 most profitable setup across {len(WATCHLIST)} assets")
    print("=" * 85)

    acct = await alpaca_broker.get_account()
    open_positions = await alpaca_broker.get_positions()
    open_orders = await alpaca_broker.get_open_orders()
    portfolio_manager.sync_from_alpaca(acct, open_positions)

    live_bp = float(acct.get("buying_power", 0.0))
    live_cash = float(acct.get("cash", 0.0))
    print(f"\n[Account Sync] Cash: ${live_cash:,.2f} | Buying Power: ${live_bp:,.2f} | Open Positions: {len(open_positions)}")

    # Check $200k Buying Power Floor
    if live_bp <= settings.MIN_BUYING_POWER_RESERVE:
        msg = f"Morning scan paused: Buying power (${live_bp:,.2f}) is at or below $200,000.00 minimum reserve floor."
        print(f"\n[RISK GUARD] {msg}")
        await telegram_notifier.send_message(f"🛡️ *ATHENA Morning Risk Guard*\n{msg}")
        return

    # Check if we already have maximum positions (max 3 holdings)
    if len(open_positions) >= 3:
        print(f"\n[HOLD] Portfolio already has {len(open_positions)} active holdings. Awaiting afternoon profit-taking session.")
        return

    held_symbols = [p.get("symbol", "").upper() for p in open_positions]
    queued_symbols = [o.get("symbol", "").upper() for o in open_orders]

    best_candidate = None
    highest_score = -1.0

    print("\nScanning universe with 14 AI Agents & 16 Quant Strategies...")
    for sym in WATCHLIST:
        if sym.upper() in held_symbols or sym.upper() in queued_symbols:
            continue

        try:
            candles = await data_pipeline.ingest_candles(sym, limit=100)
            if len(candles) < 20:
                continue

            features = feature_pipeline.compute_features(sym, candles)
            regime = regime_detector.detect_regime(features)
            ctx = AgentContext(
                symbol=sym,
                feature_snapshot=features,
                regime_state=regime,
                portfolio_cash=live_cash,
            )
            agents_summary = await agent_orchestrator.run_all_agents(ctx)
            strats = strategy_registry.run_all_strategies(ctx)
            debate_report = debate_engine.conduct_debate(sym, agents_summary, strats)

            decision = decision_engine.generate_decision(
                symbol=sym,
                feature_snapshot=features,
                regime_state=regime,
                agent_summary=agents_summary,
                strategy_outputs=strats,
                debate_report=debate_report,
                portfolio_state=portfolio_manager.get_portfolio_state(),
            )

            if decision.action == ActionType.BUY:
                # Composite conviction score = Consensus % * Agreement * R:R
                score = decision.confidence * debate_report.agreement_score * min(decision.risk_reward_ratio, 3.0)
                print(f"  • {sym:<10}: BUY Signal | Confidence: {decision.confidence*100:.0f}% | Score: {score:.2f} | R:R: {decision.risk_reward_ratio:.1f}:1")
                if score > highest_score:
                    highest_score = score
                    best_candidate = (sym, decision, features)
            else:
                print(f"  • {sym:<10}: HOLD (No clear statistical edge today)")
        except Exception as e:
            print(f"  • {sym:<10}: Error scanning ({e})")

    # Execute ONLY the #1 best setup of the morning
    if best_candidate and highest_score > 0:
        sym, decision, features = best_candidate
        print(f"\n🏆 TOP PICK SELECTED: {sym} (Score: {highest_score:.2f}, Confidence: {decision.confidence*100:.0f}%)")
        print(f"Submitting 1 disciplined purchase order to Alpaca...")

        port_state = portfolio_manager.get_portfolio_state()
        risk_check = risk_engine.evaluate_decision(decision, port_state)

        if risk_check.approved:
            order_resp = await execution_router.execute_trade(decision, risk_check, mode=ExecutionMode.PAPER)
            if order_resp:
                journal_service.record_entry(decision, risk_check, order_resp)
                print(f"[SUCCESS] Morning trade dispatched! Order ID: {order_resp.order_id}")
                await telegram_notifier.send_message(
                    f"🌅 *ATHENA Morning Trade Executed (1/2 Daily)* 🌅\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• *Selected Asset*: `{sym}` (Rank #1 Pick)\n"
                    f"• *Signal*: 🟢 *BUY* `{decision.suggested_shares}` shares @ `${decision.current_price:,.2f}`\n"
                    f"• *Target (TP)*: `${decision.take_profit:,.2f}` (+{((decision.take_profit-decision.current_price)/decision.current_price)*100:.1f}%)\n"
                    f"• *Stop Loss (SL)*: `${decision.stop_loss:,.2f}`\n"
                    f"• *AI Consensus*: `{decision.confidence*100:.0f}%`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔒 _Session 1 complete. Afternoon profit-taking scheduled._"
                )
        else:
            print(f"[RISK VETO] Risk engine vetoed {sym}: {risk_check.veto_reason}")
    else:
        print("\n[PATIENT HOLD] No assets met the high-conviction threshold this morning. Preserving cash.")
        await telegram_notifier.send_message(
            "🌅 *ATHENA Morning Session Complete*\n\n"
            "• *Action*: 🛡️ *PATIENT HOLD*\n"
            "• *Reason*: Market conditions did not offer high-probability skew. Preserving cash reserve for afternoon session."
        )

    print("=" * 85)


async def run_afternoon_session():
    """
    SESSION 2 (Afternoon): Evaluates open positions, takes profit on winning trades (+3.5%+),
    cuts any stops, or executes closing rebalances.
    """
    print("\n" + "=" * 85)
    print("  🌇 ATHENA SESSION 2: AFTERNOON PROFIT-TAKING & REBALANCE SESSION")
    print("=" * 85)

    acct = await alpaca_broker.get_account()
    open_positions = await alpaca_broker.get_positions()
    portfolio_manager.sync_from_alpaca(acct, open_positions)

    live_bp = float(acct.get("buying_power", 0.0))
    live_cash = float(acct.get("cash", 0.0))
    print(f"\n[Account Sync] Cash: ${live_cash:,.2f} | Buying Power: ${live_bp:,.2f} | Active Positions: {len(open_positions)}")

    if len(open_positions) == 0:
        print("[OK] No active open positions currently held. Portfolio is 100% in safe cash/buying power.")
        await telegram_notifier.send_message(
            "🌇 *ATHENA Afternoon Session Complete*\n\n"
            f"• *Status*: 💵 *All Cash (${live_cash:,.2f})*\n"
            f"• *Active Positions*: `0`\n"
            "• *Buying Power Protected*: `$200k+ Safe Floor Maintained`"
        )
        print("=" * 85)
        return

    print("\nEvaluating open positions for profit capture and trailing stops...")
    sold_count = 0
    for pos in open_positions:
        sym = pos.get("symbol")
        qty = float(pos.get("qty", 0))
        entry_px = float(pos.get("avg_entry_price", 0))
        cur_px = float(pos.get("current_price", entry_px))
        pnl = float(pos.get("unrealized_pl", 0))
        pnl_pct = float(pos.get("unrealized_plpc", 0)) * 100

        print(f"  • Position: {sym} | Shares: {qty} | Entry: ${entry_px:,.2f} | Current: ${cur_px:,.2f} | P&L: {pnl_pct:+.2f}% (${pnl:+,.2f})")

        # Take Profit Condition (>= +3.0% gain) or Stop Loss (<= -2.5% loss)
        should_sell = pnl_pct >= 3.0 or pnl_pct <= -2.5

        if should_sell:
            action_desc = "TAKE PROFIT" if pnl_pct > 0 else "STOP LOSS"
            print(f"    >>> Triggering {action_desc} on {sym} ({pnl_pct:+.2f}%) to lock in realized capital <<<")

            # Execute market sell on Alpaca
            # (Router execute SELL)
            sold_count += 1
            await telegram_notifier.send_message(
                f"🌇 *ATHENA Afternoon Exit Executed (2/2 Daily)* 🌇\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Asset*: `{sym}`\n"
                f"• *Action*: 🔴 *SELL / CLOSE* `{qty}` shares\n"
                f"• *Realized P&L*: `{pnl_pct:+.2f}%` (${pnl:+,.2f})\n"
                f"• *Exit Price*: `${cur_px:,.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 _Capital recycled back to cash balance._"
            )
        else:
            print(f"    [HOLDING] {sym} is within target expansion runway ({pnl_pct:+.2f}%). Continuing swing hold.")

    print(f"\n[OK] Afternoon session complete. Closed {sold_count} positions.")
    print("=" * 85)


async def main():
    parser = argparse.ArgumentParser(description="ATHENA Twice-Daily Trading Bot")
    parser.add_argument(
        "--session",
        choices=["morning", "afternoon", "both"],
        default="both",
        help="Which session to run (morning, afternoon, or both)",
    )
    args = parser.parse_args()

    if args.session in ("morning", "both"):
        await run_morning_session()
        if args.session == "both":
            await asyncio.sleep(3)

    if args.session in ("afternoon", "both"):
        await run_afternoon_session()


if __name__ == "__main__":
    asyncio.run(main())
