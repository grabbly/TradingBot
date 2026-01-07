#!/usr/bin/env python3
"""
Load historical OHLC data from Yahoo Finance and calculate EMA for visualization
Supports any stock symbol, flexible timeframes, and easy data backfilling
"""

import os
import sys
try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Installing...")
    os.system("pip3 install yfinance --break-system-packages 2>/dev/null || pip3 install yfinance --user")
    import yfinance as yf

import psycopg2
from datetime import datetime, timedelta

# DB config
DB_CONFIG = {
    'host': os.environ.get('PGHOST', 'localhost'),
    'port': int(os.environ.get('PGPORT', '5432')),
    'dbname': os.environ.get('PGDATABASE', 'trading_bot'),
    'user': os.environ.get('PGUSER', 'n8n_user'),
    'password': os.environ.get('PGPASSWORD', '***REMOVED***'),
}


def calculate_ema(prices, period):
    """Calculate EMA for given prices. Returns full-length array with None for first period-1 values"""
    ema = [None] * (period - 1)  # Fill first period-1 values with None
    multiplier = 2 / (period + 1)
    
    # Initial SMA
    sma = sum(prices[:period]) / period
    ema.append(sma)
    
    # Calculate EMA for rest
    for i in range(period, len(prices)):
        ema_val = (prices[i] - ema[-1]) * multiplier + ema[-1]
        ema.append(ema_val)
    
    return ema


def fetch_bars_yahoo(symbol, interval='5m', period='7d'):
    """
    Fetch historical bars from Yahoo Finance
    
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    print(f"Fetching {symbol} data: interval={interval}, period={period}")
    ticker = yf.Ticker(symbol)
    
    # Download data
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        print(f"No data returned for {symbol}")
        return []
    
    # Convert to list of dicts (like Alpaca format)
    bars = []
    for timestamp, row in df.iterrows():
        bars.append({
            't': timestamp.isoformat(),
            'o': float(row['Open']),
            'h': float(row['High']),
            'l': float(row['Low']),
            'c': float(row['Close']),
            'v': int(row['Volume']),
        })
    
    return bars


def process_and_save(symbol, interval='5m', period='7d'):
    """Fetch bars, calculate EMA, and save to database"""
    bars = fetch_bars_yahoo(symbol, interval, period)
    
    if len(bars) < 21:
        print(f"Not enough bars: {len(bars)} < 21")
        return
    
    print(f"Got {len(bars)} bars")
    
    # Calculate EMAs for all periods
    closes = [float(bar['c']) for bar in bars]
    periods = [5, 8, 9, 13, 20, 21, 34, 50, 100, 200]
    emas = {}
    
    for period in periods:
        if len(closes) >= period:
            emas[period] = calculate_ema(closes, period)
        else:
            emas[period] = [None] * len(closes)
    
    # Prepare data for insert (skip first bars where not all EMAs are calculated)
    max_period = max([p for p in periods if len(closes) >= p], default=5)
    start_idx = max_period
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for i in range(start_idx, len(bars)):
        bar = bars[i]
        timestamp = bar['t']
        close_price = float(bar['c'])
        
        # Get EMA values for this bar
        ema_vals = {period: emas[period][i] for period in periods}
        
        # Simple crossover detection (using ema5 and ema20)
        crossover = 'none'
        if i > start_idx and ema_vals[5] and ema_vals[20]:
            prev_ema5 = emas[5][i - 1]
            prev_ema20 = emas[20][i - 1]
            
            if prev_ema5 and prev_ema20:
                if prev_ema5 <= prev_ema20 and ema_vals[5] > ema_vals[20]:
                    crossover = 'bullish'
                elif prev_ema5 >= prev_ema20 and ema_vals[5] < ema_vals[20]:
                    crossover = 'bearish'
        
        try:
            cursor.execute(
                """
                INSERT INTO ema_snapshots 
                (timestamp, symbol, close_price, ema5, ema8, ema9, ema13, ema20, ema21, ema34, ema50, ema100, ema200, action, crossover, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (timestamp, symbol, close_price, 
                 ema_vals[5], ema_vals[8], ema_vals[9], ema_vals[13], 
                 ema_vals[20], ema_vals[21], ema_vals[34], ema_vals[50], 
                 ema_vals[100], ema_vals[200],
                 'hold', crossover, 'Historical data')
            )
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"Error inserting bar {i}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {inserted} rows, skipped {skipped} duplicates")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Load historical stock data from Yahoo Finance',
        epilog='''
Examples:
  # Load 7 days of 5-minute data for NVDA
  %(prog)s --symbol NVDA --interval 5m --period 7d
  
  # Load 1 year of daily data for AAPL
  %(prog)s --symbol AAPL --interval 1d --period 1y
  
  # Load 3 months of hourly data for TSLA
  %(prog)s --symbol TSLA --interval 1h --period 3mo

Intervals: 1m, 2m, 5m, 15m, 30m, 60m, 1h, 1d, 1wk, 1mo
Periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--symbol', default='NVDA', help='Stock symbol (default: NVDA)')
    parser.add_argument('--interval', default='5m', help='Data interval (default: 5m)')
    parser.add_argument('--period', default='7d', help='Time period to fetch (default: 7d)')
    parser.add_argument('--batch', nargs='+', help='Load multiple symbols: --batch NVDA AAPL TSLA')
    
    args = parser.parse_args()
    
    if args.batch:
        print(f"Batch mode: loading {len(args.batch)} symbols")
        for sym in args.batch:
            print(f"\n{'='*60}")
            print(f"Processing {sym}...")
            print('='*60)
            try:
                process_and_save(sym, args.interval, args.period)
            except Exception as e:
                print(f"ERROR loading {sym}: {e}")
        print(f"\n{'='*60}")
        print("Batch processing complete!")
    else:
        process_and_save(args.symbol, args.interval, args.period)
    
    print("\n✅ Done! Check https://treddy.acebox.eu")
