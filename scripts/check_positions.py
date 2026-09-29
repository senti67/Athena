import os
import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("ALPACA_API_KEY")
secret = os.getenv("ALPACA_SECRET_KEY")
headers = {
    "APCA-API-KEY-ID": key,
    "APCA-API-SECRET-KEY": secret
}

acct = httpx.get("https://paper-api.alpaca.markets/v2/account", headers=headers).json()
positions = httpx.get("https://paper-api.alpaca.markets/v2/positions", headers=headers).json()

print(f"=== ALPACA ACCOUNT SNAPSHOT ===")
print(f"NAV / Portfolio Value : ${float(acct.get('portfolio_value', 0)):,.2f}")
print(f"Liquid Cash           : ${float(acct.get('cash', 0)):,.2f}")
print(f"Buying Power          : ${float(acct.get('buying_power', 0)):,.2f}")
print(f"Active Positions      : {len(positions)}")
print("-" * 65)
for p in positions:
    sym = p["symbol"]
    qty = p["qty"]
    entry = float(p["avg_entry_price"])
    curr = float(p["current_price"])
    val = float(p["market_value"])
    pnl = float(p["unrealized_pl"])
    pnl_pct = float(p["unrealized_plpc"]) * 100
    print(f" • {sym:<8} | Qty: {qty:>4} | Entry: ${entry:>8.2f} | Current: ${curr:>8.2f} | Val: ${val:>10.2f} | PnL: ${pnl:>8.2f} ({pnl_pct:>+6.2f}%)")
print("=" * 65)
