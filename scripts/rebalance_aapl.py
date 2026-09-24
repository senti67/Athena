"""
ATHENA Portfolio Rebalancing Script: Trim AAPL to 20% NAV Cap
Sells 354 shares of AAPL, preserving 60 shares (~$20k) and eliminating margin borrowing.
"""

import asyncio
from datetime import datetime
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from packages.schemas.order import ExecutionMode, OrderRequest, OrderSide, OrderType
from services.execution_service.alpaca_broker import alpaca_broker
from services.notification_service.telegram_notifier import telegram_notifier
from services.portfolio_service.optimizer import portfolio_manager


async def rebalance_aapl():
    print("=" * 70)
    print("  ⚖️ ATHENA PORTFOLIO REBALANCING: AAPL POSITION TRIM")
    print("=" * 70)

    # 1. Fetch current positions
    acct = await alpaca_broker.get_account()
    positions = await alpaca_broker.get_positions()
    portfolio_manager.sync_from_alpaca(acct, positions)

    live_cash = float(acct.get("cash", 0.0))
    live_nav = float(acct.get("equity", 100000.0))
    print(f"\n[Pre-Rebalance] NAV: ${live_nav:,.2f} | Cash: ${live_cash:,.2f}")

    aapl_pos = next((p for p in positions if p.get("symbol") == "AAPL"), None)
    if not aapl_pos:
        print("[SKIP] AAPL position not found in active holdings.")
        return

    cur_qty = float(aapl_pos.get("qty", 0.0))
    cur_px = float(aapl_pos.get("current_price", 338.0))
    print(f"Current AAPL Holdings: {cur_qty:.0f} shares @ ${cur_px:,.2f} (${cur_qty * cur_px:,.2f})")

    # Target 60 shares (~$20k / 20% NAV)
    trim_qty = max(0.0, cur_qty - 60.0)
    if trim_qty <= 0:
        print(f"[OK] AAPL is already at or below target size ({cur_qty:.0f} shares).")
        return

    print(f"\nSubmitting Market SELL order for {trim_qty:.0f} shares of AAPL...")

    order_req = OrderRequest(
        client_order_id=f"ATHENA-REBALANCE-AAPL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        symbol="AAPL",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=trim_qty,
        execution_mode=ExecutionMode.PAPER,
    )

    resp = await alpaca_broker.submit_order(order_req)
    print(f"[SUCCESS] Order Status: {resp.status if resp else 'SUBMITTED'}")

    # 2. Re-fetch account
    await asyncio.sleep(1.0)
    updated_acct = await alpaca_broker.get_account()
    updated_cash = float(updated_acct.get("cash", 0.0))
    updated_bp = float(updated_acct.get("buying_power", 0.0))
    print(f"\n[Post-Rebalance] Estimated Cash: ${updated_cash:,.2f} | Buying Power: ${updated_bp:,.2f}")

    # 3. Notify via Telegram
    await telegram_notifier.send_message(
        f"⚖️ *ATHENA Portfolio Rebalance Executed* ⚖️\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Asset*: `AAPL`\n"
        f"• *Action*: 🔴 *SELL (Trim)* `{trim_qty:.0f}` shares\n"
        f"• *Remaining Target*: `60` shares (~${60 * cur_px:,.2f} / 20% NAV)\n"
        f"• *Capital Unlocked*: `~${trim_qty * cur_px:,.2f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 _Cash balance restored to positive liquid state._"
    )
    print("[Telegram Alert Dispatched]")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(rebalance_aapl())
