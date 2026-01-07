#!/usr/bin/env python3
"""
Recalculate EMA values for historical data in ema_snapshots table.
Adds EMA periods: 8, 9, 13, 21, 34, 50, 100, 200
"""

import psycopg2
import sys
from datetime import datetime

# Database connection settings
DB_CONFIG = {
    'database': 'trading_bot',
    'user': 'postgres'
}

def calculate_ema(prices, period):
    """
    Calculate EMA for a series of prices.
    
    Args:
        prices: List of prices (oldest first)
        period: EMA period
    
    Returns:
        List of EMA values
    """
    if not prices or len(prices) == 0:
        return []
    
    multiplier = 2 / (period + 1)
    ema_values = []
    
    # First EMA is just the first price (or could use SMA of first 'period' values)
    ema = prices[0]
    ema_values.append(ema)
    
    # Calculate subsequent EMAs
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
        ema_values.append(ema)
    
    return ema_values


def recalculate_emas(conn):
    """Recalculate all EMA values for historical data."""
    
    cursor = conn.cursor()
    
    # Get all records with close_price, ordered by timestamp
    print("Loading historical data...")
    cursor.execute("""
        SELECT id, timestamp, symbol, close_price
        FROM ema_snapshots
        WHERE close_price IS NOT NULL
        ORDER BY symbol, timestamp
    """)
    
    records = cursor.fetchall()
    print(f"Loaded {len(records)} records")
    
    if not records:
        print("No records with close_price found!")
        return
    
    # Group by symbol
    symbol_data = {}
    for record in records:
        rec_id, timestamp, symbol, close_price = record
        if symbol not in symbol_data:
            symbol_data[symbol] = []
        symbol_data[symbol].append({
            'id': rec_id,
            'timestamp': timestamp,
            'price': float(close_price)
        })
    
    print(f"Processing {len(symbol_data)} symbols...")
    
    # Calculate EMAs for each symbol
    periods = [8, 9, 13, 21, 34, 50, 100, 200]
    total_updates = 0
    
    for symbol, data in symbol_data.items():
        print(f"\nProcessing {symbol}: {len(data)} records")
        
        # Extract prices
        prices = [d['price'] for d in data]
        
        # Calculate EMAs for all periods
        ema_results = {}
        for period in periods:
            print(f"  Calculating EMA{period}...", end='', flush=True)
            ema_results[period] = calculate_ema(prices, period)
            print(f" done")
        
        # Update database in batches
        print(f"  Updating database...", end='', flush=True)
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            # Prepare update query
            update_values = []
            for j, record in enumerate(batch):
                idx = i + j
                rec_id = record['id']
                values = [
                    rec_id,
                    round(ema_results[8][idx], 4),
                    round(ema_results[9][idx], 4),
                    round(ema_results[13][idx], 4),
                    round(ema_results[21][idx], 4),
                    round(ema_results[34][idx], 4),
                    round(ema_results[50][idx], 4),
                    round(ema_results[100][idx], 4),
                    round(ema_results[200][idx], 4)
                ]
                update_values.append(values)
            
            # Execute batch update
            cursor.executemany("""
                UPDATE ema_snapshots
                SET ema8 = %s, ema9 = %s, ema13 = %s, ema21 = %s,
                    ema34 = %s, ema50 = %s, ema100 = %s, ema200 = %s
                WHERE id = %s
            """, [(v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[0]) for v in update_values])
            
            conn.commit()
            total_updates += len(batch)
        
        print(f" updated {len(data)} records")
    
    print(f"\n✅ Total records updated: {total_updates}")
    cursor.close()


def main():
    """Main execution function."""
    
    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected successfully")
        
        # Recalculate EMAs
        recalculate_emas(conn)
        
        # Verify results
        print("\nVerifying results...")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(ema8) as with_ema8,
                COUNT(ema200) as with_ema200
            FROM ema_snapshots
            WHERE close_price IS NOT NULL
        """)
        total, with_ema8, with_ema200 = cursor.fetchone()
        print(f"Total records: {total}")
        print(f"With EMA8: {with_ema8}")
        print(f"With EMA200: {with_ema200}")
        
        # Show sample
        cursor.execute("""
            SELECT timestamp, symbol, close_price, ema5, ema8, ema20, ema21, ema50, ema200
            FROM ema_snapshots
            WHERE close_price IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        print("\nSample of recent data:")
        print("Timestamp            | Symbol | Price    | EMA5     | EMA8     | EMA20    | EMA21    | EMA50    | EMA200")
        print("-" * 110)
        for row in cursor.fetchall():
            print(f"{row[0]} | {row[1]:6} | {row[2]:8.2f} | {row[3]:8.2f} | {row[4]:8.2f} | {row[5]:8.2f} | {row[6]:8.2f} | {row[7]:8.2f} | {row[8]:8.2f}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ EMA recalculation completed successfully!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
