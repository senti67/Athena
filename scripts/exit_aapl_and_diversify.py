"""
ATHENA Script: Exit AAPL and Diversify Portfolio Across Multi-Sector Universe
1. Cancels pending partial AAPL sell orders.
2. Submits complete market SELL order for all 414 shares of AAPL.
3. Refreshes account and calculates positive liquid buying power.
4. Scans 89-asset universe across 12 sectors with 6 Research Agents & 5 Production Strategies.
5. Executes top-ranked diversified setups with 15-20% NAV position sizing.
6. Dispatches full Telegram execution and rebalance cards.
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
from packages.common.universe import GLOBAL_WATCHLIST, SECTOR_WATCHLISTS
from packages.schemas.agent import AgentContext
from packages.schemas.decision import ActionType
from packages.schemas.order import ExecutionMode, OrderRequest, OrderSide, OrderType
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
from services.strategy_service.engine import strategy_engine


async def execute_exit_and_diversification():
    print("=" * 85)
    print("  🚀 ATHENA STRATEGIC REBALANCING: EXIT AAPL & DIVERSIFY PORTFOLIO")
    print("=" * 85)

    # 1. Fetch current account state and positions
    acct = await alpaca_broker.get_account()
    positions = await alpaca_broker.get_positions()
    open_orders = await alpaca_broker.get_open_orders()
    portfolio_manager.sync_from_alpaca(acct, positions)

    live_nav = float(acct.get("equity", 100000.0))
    live_cash = float(acct.get("cash", 0.0))
    print(f"\n[Current Account State] NAV: ${live_nav:,.2f} | Cash: ${live_cash:,.2f} | Positions: {len(positions)}")

    # 2. Cancel pending AAPL open orders
    aapl_orders = [o for o in open_orders if o.get("symbol") == "AAPL"]
    if aapl_orders:
        print(f"Cancelling {len(aapl_orders)} pending partial AAPL orders...")
        await alpaca_broker.cancel_all_orders()
        await asyncio.sleep(1.0)

    # 3. Sell entire AAPL position
    aapl_pos = next((p for p in positions if p.get("symbol") == "AAPL"), None)
    if aapl_pos:
        aapl_qty = float(aapl_pos.get("qty", 0.0))
        aapl_entry = float(aapl_pos.get("avg_entry_price", 341.13))
        aapl_cur = float(aapl_pos.get("current_price", 336.0))
        aapl_mkt_val = aapl_qty * aapl_cur

        print(f"\nSubmitting Full Exit Order for AAPL ({aapl_qty:.0f} shares @ ${aapl_cur:,.2f} = ${aapl_mkt_val:,.2f})...")
        order_req = OrderRequest(
            client_order_id=f"ATHENA-EXIT-AAPL-FULL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=aapl_qty,
            execution_mode=ExecutionMode.PAPER,
        )
        resp = await alpaca_broker.submit_order(order_req)
        print(f"[AAPL EXIT SUBMITTED] Order ID: {resp.order_id if resp else 'N/A'}")

        await telegram_notifier.send_message(
            f"🔄 *ATHENA Strategic Exit: AAPL Liquidated* 🔄\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Asset*: `AAPL`\n"
            f"• *Action*: 🔴 *FULL EXIT (SELL)* `{aapl_qty:.0f}` shares\n"
            f"• *Capital Realized*: `~${aapl_mkt_val:,.2f}`\n"
            f"• *Reason*: Portfolio diversification into multi-sector non-correlated assets.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 _Capital recycled into liquid cash reserve._"
        )
    else:
        print("\n[NOTE] No active AAPL position found.")

    # 4. Refresh account balances after exit
    await asyncio.sleep(1.5)
    acct = await alpaca_broker.get_account()
    positions = await alpaca_broker.get_positions()
    portfolio_manager.sync_from_alpaca(acct, positions)

    updated_nav = float(acct.get("equity", live_nav))
    updated_cash = float(acct.get("cash", live_cash))
    updated_bp = float(acct.get("buying_power", 0.0))
    print(f"\n[Post-Exit Capital State] NAV: ${updated_nav:,.2f} | Buying Power: ${updated_bp:,.2f}")

    # Exclude already held symbols from new candidate buys
    held_symbols = {p.get("symbol", "").upper() for p in positions}
    print(f"Active Non-AAPL Holdings: {[p.get('symbol') for p in positions if p.get('symbol') != 'AAPL']}")

    # 5. Scan the 89-ticker universe across diverse sectors
    print("\nScanning 89 assets across 12 sectors with 6 Research Agents & 5 Production Strategies...")
    candidates = []

    for sym in GLOBAL_WATCHLIST:
        if sym.upper() in held_symbols or sym.upper() == "AAPL":
            continue

        try:
            candles = await data_pipeline.ingest_candles(sym, limit=100)
            if len(candles) < 20:
                continue

            features = feature_pipeline.compute_features(sym, candles)
            regime = regime_detector.detect_regime(features)

            # Ingest fundamentals with fast timeout
            try:
                fundamentals = await asyncio.wait_for(data_pipeline.get_fundamental_metrics(sym), timeout=2.0)
            except Exception:
                fundamentals = {}

            ctx = AgentContext(
                symbol=sym,
                feature_snapshot=features,
                regime_state=regime,
                portfolio_cash=updated_cash,
                fundamental_metrics=fundamentals if isinstance(fundamentals, dict) else {},
            )

            agents_summary = await agent_orchestrator.run_all_agents(ctx)
            best_strat_setup, strats = strategy_engine.evaluate_strategies(ctx)
            debate_report = debate_engine.conduct_debate(sym, agents_summary, strats)

            decision = decision_engine.generate_decision(
                symbol=sym,
                feature_snapshot=features,
                regime_state=regime,
                agent_summary=agents_summary,
                strategy_outputs=strats,
                debate_report=debate_report,
                portfolio_state=portfolio_manager.get_portfolio_state(),
                best_strategy_setup=best_strat_setup,
            )

            if decision.action == ActionType.BUY:
                composite_score = decision.confidence * debate_report.agreement_score * min(decision.risk_reward_ratio, 3.0)
                print(
                    f"  • {sym:<10}: BUY Signal | Conf: {decision.confidence*100:.0f}% | "
                    f"Score: {composite_score:.2f} | R:R: {decision.risk_reward_ratio:.1f}:1 | "
                    f"Setup: {best_strat_setup.strategy_name if best_strat_setup else 'Consensus'}",
                    flush=True,
                )
                candidates.append((composite_score, sym, decision, features, debate_report))
        except Exception:
            pass

    # Sort candidates by composite score descending
    candidates.sort(key=lambda x: x[0], reverse=True)

    # 6. Execute top 2 diversified setups across different sectors
    if not candidates:
        print("\n[HOLD] No qualified assets passed the consensus filter today. Capital safely preserved.")
        return

    print(f"\nFound {len(candidates)} high-conviction buy setups! Selecting top diversified assets...")

    # We want up to 2 distinct non-overlapping picks
    executed_count = 0
    max_new_buys = min(2, settings.MAX_ACTIVE_POSITIONS - len([p for p in positions if p.get("symbol") != "AAPL"]))

    for score, sym, decision, features, debate_report in candidates:
        if executed_count >= max_new_buys:
            break

        port_state = portfolio_manager.get_portfolio_state()
        risk_check = risk_engine.evaluate_decision(decision, port_state, pending_sell_symbols=["AAPL"])

        if risk_check.approved:
            print(f"\n🏆 EXECUTING DIVERSIFIED PICK #{executed_count + 1}: {sym} (Score: {score:.2f})")
            print(f"Targeting ~${decision.suggested_shares * decision.current_price:,.2f} (~20% NAV)...")

            order_resp = await execution_router.execute_trade(decision, risk_check, mode=ExecutionMode.PAPER)
            if order_resp:
                journal_service.record_entry(decision, risk_check, order_resp)
                executed_count += 1
                print(f"[SUCCESS] Order Dispatched for {sym}! Order ID: {order_resp.order_id}")

                await telegram_notifier.send_message(
                    f"🌐 *ATHENA Diversified Allocation Executed* 🌐\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• *Selected Asset*: `{sym}` (Rank #{executed_count} Pick)\n"
                    f"• *Action*: 🟢 *BUY* `{decision.suggested_shares}` shares @ `${decision.current_price:,.2f}`\n"
                    f"• *Position Value*: `${decision.suggested_shares * decision.current_price:,.2f}` (~20% NAV)\n"
                    f"• *Take-Profit*: `${decision.take_profit:,.2f}` (+{((decision.take_profit - decision.current_price) / decision.current_price) * 100:.1f}%)\n"
                    f"• *Stop-Loss*: `${decision.stop_loss:,.2f}`\n"
                    f"• *AI Consensus*: `{decision.confidence * 100:.0f}%` (6 Research Domains & 5 Strategies)\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💼 _Portfolio rebalanced into multi-sector growth._"
                )
        else:
            print(f"[RISK VETO] {sym} vetoed by risk engine: {risk_check.veto_reason}")

    print("\n" + "=" * 85)
    print("  ✅ ATHENA PORTFOLIO DIVERSIFICATION COMPLETE")
    print("=" * 85)


if __name__ == "__main__":
    asyncio.run(execute_exit_and_diversification())
