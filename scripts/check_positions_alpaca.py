#!/usr/bin/env python3
"""
Check current Alpaca positions and P&L
"""
import requests
import json
import os
from datetime import datetime

# Alpaca Paper Trading API
BASE_URL = os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

# Load credentials from environment variables
API_KEY = os.environ.get('ALPACA_API_KEY')
API_SECRET = os.environ.get('ALPACA_SECRET_KEY')

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

def get_account():
    """Get account info"""
    response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Account error: {response.status_code} - {response.text}")
        return None

def get_positions():
    """Get all open positions"""
    response = requests.get(f"{BASE_URL}/v2/positions", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Positions error: {response.status_code} - {response.text}")
        return []

def get_orders():
    """Get all orders (including stop-loss and take-profit)"""
    response = requests.get(f"{BASE_URL}/v2/orders?status=all&limit=50", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Orders error: {response.status_code} - {response.text}")
        return []

def main():
    print("=" * 80)
    print("📊 ALPACA PORTFOLIO STATUS")
    print("=" * 80)
    print()
    
    # Account info
    account = get_account()
    if account:
        equity = float(account.get('equity', 0))
        last_equity = float(account.get('last_equity', 0))
        cash = float(account.get('cash', 0))
        buying_power = float(account.get('buying_power', 0))
        daily_pnl = equity - last_equity
        daily_pnl_pct = (daily_pnl / last_equity * 100) if last_equity > 0 else 0
        
        print(f"💰 Total Equity: ${equity:,.2f}")
        print(f"📈 Daily P&L: ${daily_pnl:+,.2f} ({daily_pnl_pct:+.2f}%)")
        print(f"💵 Cash: ${cash:,.2f}")
        print(f"📦 Buying Power: ${buying_power:,.2f}")
        print()
    
    # Positions
    positions = get_positions()
    if positions:
        print("=" * 80)
        print(f"📍 OPEN POSITIONS ({len(positions)})")
        print("=" * 80)
        
        for pos in positions:
            symbol = pos['symbol']
            qty = float(pos['qty'])
            entry_price = float(pos['avg_entry_price'])
            current_price = float(pos['current_price'])
            market_value = float(pos['market_value'])
            unrealized_pl = float(pos['unrealized_pl'])
            unrealized_plpc = float(pos['unrealized_plpc']) * 100
            
            emoji = "🟢" if unrealized_pl >= 0 else "🔴"
            
            print(f"\n{emoji} {symbol}")
            print(f"   Qty: {qty}")
            print(f"   Entry: ${entry_price:.2f}")
            print(f"   Current: ${current_price:.2f}")
            print(f"   Market Value: ${market_value:,.2f}")
            print(f"   Unrealized P&L: ${unrealized_pl:+,.2f} ({unrealized_plpc:+.2f}%)")
        
        print()
    else:
        print("📭 No open positions")
        print()
    
    # Recent orders
    orders = get_orders()
    if orders:
        print("=" * 80)
        print(f"📋 RECENT ORDERS (Last 10)")
        print("=" * 80)
        
        for order in orders[:10]:
            symbol = order['symbol']
            side = order['side'].upper()
            qty = order['qty']
            order_type = order['type']
            status = order['status']
            created_at = order['created_at'][:19].replace('T', ' ')
            
            emoji = "🟢" if side == "BUY" else "🔴"
            
            print(f"{emoji} {symbol} {side} {qty} ({order_type}) - {status} @ {created_at}")
        
        print()
    
    print("=" * 80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
