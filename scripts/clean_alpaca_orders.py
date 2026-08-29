"""
ATHENA Alpaca Order Book Cleanup Utility
Cancels all pending / queued orders on Alpaca Paper Account to restore full buying power.
"""

import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.execution_service.alpaca_broker import alpaca_broker


async def clean_alpaca():
    print("=" * 75)
    print("  ATHENA ALPACA ORDER BOOK CLEANUP & MARGIN RESET")
    print("=" * 75)

    acct_before = await alpaca_broker.get_account()
    open_orders_before = await alpaca_broker.get_open_orders()

    print(f"\n[+] Connected to Alpaca Account: {acct_before.get('account_number')}")
    print(f"    Current Buying Power: ${float(acct_before.get('buying_power', 0)):,.2f}")
    print(f"    Active Queued Orders: {len(open_orders_before)}")

    if len(open_orders_before) == 0:
        print("\n[OK] No pending orders to cancel. Buying power is clean.")
        print("=" * 75)
        return

    print(f"\n[+] Cancelling all {len(open_orders_before)} queued orders to restore buying power...")
    success = await alpaca_broker.cancel_all_orders()

    if success:
        print("[OK] All queued orders successfully cancelled!")
        await asyncio.sleep(2)
        acct_after = await alpaca_broker.get_account()
        print(f"\n[+] Updated Account State:")
        print(f"    Restored Buying Power: ${float(acct_after.get('buying_power', 0)):,.2f}")
        print(f"    Available Cash: ${float(acct_after.get('cash', 0)):,.2f}")
    else:
        print("[X] Could not cancel orders. Check API connection.")

    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(clean_alpaca())
