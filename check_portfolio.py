#!/usr/bin/env python3
"""Check Alpaca portfolio status and P&L"""
import requests
import os
from datetime import datetime

# Load credentials from environment variables
API_KEY = os.environ.get('ALPACA_API_KEY')
API_SECRET = os.environ.get('ALPACA_SECRET_KEY')
BASE_URL = os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

if not API_KEY or not API_SECRET:
    print("❌ Error: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment")
    print("   Set them in .env file or export them:")
    print("   export ALPACA_API_KEY=your_key")
    print("   export ALPACA_SECRET_KEY=your_secret")
    exit(1)

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

print("=" * 80)
print("📊 ALPACA PORTFOLIO STATUS")
print("=" * 80)
print()

account_resp = requests.get(f"{BASE_URL}/v2/account", headers=headers)
if account_resp.status_code != 200:
    print(f"❌ Error: {account_resp.status_code}")
    print(account_resp.text)
    exit(1)

account = account_resp.json()
equity = float(account.get('equity', 0))
last_equity = float(account.get('last_equity', 0))
cash = float(account.get('cash', 0))
daily_pnl = equity - last_equity
daily_pnl_pct = (daily_pnl / last_equity * 100) if last_equity > 0 else 0

print(f"💰 Total Equity: ${equity:,.2f}")
print(f"📈 Daily P&L: ${daily_pnl:+,.2f} ({daily_pnl_pct:+.2f}%)")
print(f"💵 Cash: ${cash:,.2f}")
print()

positions = requests.get(f"{BASE_URL}/v2/positions", headers=headers).json()
if positions:
    print("=" * 80)
    print(f"📍 OPEN POSITIONS ({len(positions)})")
    print("=" * 80)
    
    # Sort by P&L
    sorted_positions = sorted(positions, key=lambda x: float(x['unrealized_pl']), reverse=True)
    
    for pos in sorted_positions:
        unrealized_pl = float(pos['unrealized_pl'])
        unrealized_plpc = float(pos['unrealized_plpc']) * 100
        emoji = "🟢" if unrealized_pl >= 0 else "🔴"
        
        print(f"\n{emoji} {pos['symbol']}")
        print(f"   Qty: {float(pos['qty']):.0f} shares")
        print(f"   Entry: ${float(pos['avg_entry_price']):.2f}")
        print(f"   Current: ${float(pos['current_price']):.2f}")
        print(f"   Market Value: ${float(pos['market_value']):,.2f}")
        print(f"   Unrealized P&L: ${unrealized_pl:+,.2f} ({unrealized_plpc:+.2f}%)")
        
        # Check if near take-profit (4%)
        if unrealized_plpc >= 3.5:
            print(f"   ⚠️  Near take-profit target (4%)")
    print()
else:
    print("📭 No open positions\n")

print("=" * 80)
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
