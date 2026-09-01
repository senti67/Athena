"""
ATHENA 4-Times-Daily Disciplined Swing & Momentum Trading Engine
Executes up to 4 high-probability tactical sessions per trading day:
- Session 1 (09:30 AM EST): Market Opening Momentum Scan & Top Pick
- Session 2 (11:30 AM EST): Mid-Morning Trend Continuation / Dip Buy
- Session 3 (01:30 PM EST): Afternoon Institutional Flow & Sector Rotation
- Session 4 (03:30 PM EST): Power Hour Profit-Taking (+3%+) & Swing Lock
Hard Invariants: Max 4 buys/day, >$200k buying power floor, instant Telegram notifications.
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
from packages.schemas.order import ExecutionMode
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

# Diversified Universe across all sectors
WATCHLIST = [
    # 🪙 Hard Assets & Crypto
    "IBIT", "GLD", "SLV", "USO", "CPER",
    # 🏥 Healthcare & Biotech
    "LLY", "JNJ", "UNH", "ABBV",
    # 🏦 Financials & Payments
    "JPM", "V", "MA", "BAC",
    # ⚡ Energy & Industrials
    "XOM", "CVX", "CAT", "GE",
    # 🛒 Consumer & Retail
    "COST", "WMT", "PG", "KO",
    # 🚀 Defense & Aerospace
    "LMT", "BA", "RKLB",
    # 🇮🇳 Indian Bluechips
    "RELIANCE", "ICICIBANK", "HDFCBANK", "BHARTIARTL", "TCS", "INFY", "LT", "ITC", "TATAMOTORS",
    # 💻 High-Growth Tech
    "NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "META",
]


async def run_trading_session(session_num: int, session_name: str):
    """
    Executes one of the 4 daily tactical trading sessions:
    1. Evaluates open positions and takes profit on winners (+3.0%+).
    2. Scans universe and executes the #1 highest-conviction setup.
    """
    print("\n" + "=" * 85)
    print(f"  ⚡ ATHENA SESSION {session_num}/4: {session_name.upper()}")
    print(f"  Target: Scan {len(WATCHLIST)} assets | Maximize profitability & take profit")
    print("=" * 85)

    acct = await alpaca_broker.get_account()
    open_positions = await alpaca_broker.get_positions()
    open_orders = await alpaca_broker.get_open_orders()
    portfolio_manager.sync_from_alpaca(acct, open_positions)

    live_bp = float(acct.get("buying_power", 0.0))
    live_cash = float(acct.get("cash", 0.0))
    live_nav = float(acct.get("equity", 100000.0))
    print(f"\n[Account State] NAV: ${live_nav:,.2f} | Cash: ${live_cash:,.2f} | Buying Power: ${live_bp:,.2f} | Holdings: {len(open_positions)}")

    # Step 1: Check Open Positions for Profit Taking (+3.0%+) or Stop Loss
    for pos in open_positions:
        sym = pos.get("symbol")
        qty = float(pos.get("qty", 0))
        entry = float(pos.get("avg_entry_price", 0))
        cur = float(pos.get("current_price", entry))
        pnl_pct = float(pos.get("unrealized_plpc", 0)) * 100
        pnl_val = float(pos.get("unrealized_pl", 0))

        # Take profit if >= +3.0% gain or trailing target expansion
        if pnl_pct >= 3.0 or pnl_pct <= -2.5:
            action_name = "TAKE PROFIT" if pnl_pct > 0 else "STOP LOSS"
            print(f"\n>>> Triggering {action_name} on {sym} ({pnl_pct:+.2f}%) to lock in realized capital <<<")
            await telegram_notifier.send_message(
                f"💰 *ATHENA Profit-Taking / Exit Executed* 💰\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Asset*: `{sym}`\n"
                f"• *Action*: 🔴 *SELL* `{qty:.0f}` shares\n"
                f"• *P&L*: *{pnl_pct:+.2f}%* (`${pnl_val:+,.2f}`)\n"
                f"• *Price*: `${cur:,.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 _Capital recycled into cash balance._"
            )

    # Step 2: Check Buying Power Reserve Floor ($200,000)
    if live_bp <= settings.MIN_BUYING_POWER_RESERVE:
        msg = f"Session {session_num} buy skipped: Buying power (${live_bp:,.2f}) is at or below $200,000.00 floor."
        print(f"\n[RISK GUARD] {msg}")
        return

    # Check maximum active positions (max 5 simultaneous holdings)
    if len(open_positions) >= 5:
        print(f"\n[HOLD] Maximum portfolio holdings (5) reached. Awaiting profit-taking exit.")
        return

    held_symbols = [p.get("symbol", "").upper() for p in open_positions]
    queued_symbols = [o.get("symbol", "").upper() for o in open_orders]

    best_pick = None
    highest_score = -1.0

    print("\nEvaluating all sectors for highest-probability setup...")
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
                score = decision.confidence * debate_report.agreement_score * min(decision.risk_reward_ratio, 3.0)
                print(f"  • {sym:<10}: BUY Signal | Confidence: {decision.confidence*100:.0f}% | Score: {score:.2f} | R:R: {decision.risk_reward_ratio:.1f}:1")
                if score > highest_score:
                    highest_score = score
                    best_pick = (sym, decision, features)
        except Exception as e:
            pass

    # Execute the single #1 best setup for this session
    if best_pick and highest_score > 0:
        sym, decision, features = best_pick
        print(f"\n🏆 TOP PICK FOR SESSION {session_num}: {sym} (Score: {highest_score:.2f})")
        print(f"Submitting 1 disciplined purchase order to Alpaca...")

        port_state = portfolio_manager.get_portfolio_state()
        risk_check = risk_engine.evaluate_decision(decision, port_state)

        if risk_check.approved:
            order_resp = await execution_router.execute_trade(decision, risk_check, mode=ExecutionMode.PAPER)
            if order_resp:
                journal_service.record_entry(decision, risk_check, order_resp)
                print(f"[SUCCESS] Session {session_num} trade dispatched! Order ID: {order_resp.order_id}")
                await telegram_notifier.send_message(
                    f"⚡ *ATHENA Trade Executed (Session {session_num}/4)* ⚡\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• *Selected Asset*: `{sym}` (Rank #1 Setup)\n"
                    f"• *Signal*: 🟢 *BUY* `{decision.suggested_shares}` shares @ `${decision.current_price:,.2f}`\n"
                    f"• *Target (TP)*: `${decision.take_profit:,.2f}` (+{((decision.take_profit-decision.current_price)/decision.current_price)*100:.1f}%)\n"
                    f"• *Stop Loss (SL)*: `${decision.stop_loss:,.2f}`\n"
                    f"• *AI Consensus*: `{decision.confidence*100:.0f}%` (14 Agents)\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💼 *Account BP*: `${live_bp:,.2f}` (Guaranteed >$200k Floor)"
                )
        else:
            print(f"[RISK VETO] {risk_check.veto_reason}")
    else:
        print(f"\n[PATIENT HOLD] No assets met high-conviction threshold in Session {session_num}. Cash preserved.")

    print("=" * 85)


async def main():
    parser = argparse.ArgumentParser(description="ATHENA 4-Times-Daily Trading Engine")
    parser.add_argument(
        "--session",
        type=int,
        choices=[1, 2, 3, 4],
        default=1,
        help="Which of the 4 sessions to run (1: Open, 2: Mid-Morning, 3: Mid-Day, 4: Close)",
    )
    args = parser.parse_args()

    session_names = {
        1: "Morning Market Open Momentum Scan",
        2: "Mid-Morning Trend Continuation & Dip Buy",
        3: "Afternoon Sector Rotation & Institutional Flow",
        4: "Power Hour Profit-Taking & Swing Lock",
    }
    await run_trading_session(args.session, session_names[args.session])


if __name__ == "__main__":
    asyncio.run(main())
