#!/usr/bin/env python3
"""Check order history and entry prices"""
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
print("📋 ORDER HISTORY - Last 20 orders")
print("=" * 80)
print()

orders = requests.get(f"{BASE_URL}/v2/orders?status=all&limit=20", headers=headers).json()

for order in orders:
    symbol = order['symbol']
    side = order['side'].upper()
    qty = order['qty']
    status = order['status']
    created_at = order['created_at'][:19].replace('T', ' ')
    filled_at = order.get('filled_at')
    if filled_at:
        filled_at = filled_at[:19].replace('T', ' ')
    else:
        filled_at = 'N/A'
    
    filled_avg_price = order.get('filled_avg_price')
    if filled_avg_price:
        filled_avg_price = f"${float(filled_avg_price):.2f}"
    else:
        filled_avg_price = 'N/A'
    
    order_type = order.get('type', 'unknown')
    order_class = order.get('order_class', 'simple')
    
    emoji = "🟢" if side == "BUY" else "🔴"
    status_emoji = "✅" if status == "filled" else "⏳" if status in ["new", "pending_new"] else "❌"
    
    print(f"{emoji} {symbol} {side} x{qty} ({order_type}/{order_class})")
    print(f"   Status: {status_emoji} {status}")
    print(f"   Created: {created_at}")
    if status == "filled" and filled_avg_price != 'N/A':
        print(f"   Filled: {filled_at}")
        print(f"   Price: {filled_avg_price}")
    print()

print("=" * 80)
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
