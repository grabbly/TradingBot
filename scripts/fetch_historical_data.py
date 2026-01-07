#!/usr/bin/env python3
"""
Fetch Historical Stock Data (2023-2025)
Task 1.1.1 - Phase 1: Validation

Fetches daily OHLCV data for specified symbols from Alpaca API
and saves to CSV files for backtesting.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import pandas as pd

# Load environment variables
load_dotenv()

# Configuration
SYMBOLS = ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA']
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)
DATA_DIR = 'data'
TIMEFRAME = TimeFrame.Day

def fetch_historical_data():
    """Fetch historical data for all symbols"""
    
    # Initialize Alpaca client
    client = StockHistoricalDataClient(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY')
    )
    
    # Create data directory if not exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print(f"📊 Fetching historical data for {len(SYMBOLS)} symbols")
    print(f"Period: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Timeframe: {TIMEFRAME}")
    print("-" * 60)
    
    results = {}
    
    for symbol in SYMBOLS:
        try:
            print(f"\nFetching {symbol}...", end=' ')
            
            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TIMEFRAME,
                start=START_DATE,
                end=END_DATE
            )
            
            # Fetch data
            bars = client.get_stock_bars(request)
            
            # Convert to DataFrame
            df = bars.df
            
            if df.empty:
                print(f"❌ No data returned")
                continue
            
            # Reset index to get timestamp as column
            df = df.reset_index()
            
            # Rename columns for clarity
            df.columns = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap']
            
            # Convert timestamp to date
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            
            # Select and reorder columns
            df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'vwap']]
            
            # Save to CSV
            filename = f"{DATA_DIR}/historical_{symbol}_2023-2025.csv"
            df.to_csv(filename, index=False)
            
            results[symbol] = {
                'bars': len(df),
                'start': df['date'].min(),
                'end': df['date'].max(),
                'file': filename
            }
            
            print(f"✅ {len(df)} bars saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results[symbol] = {'error': str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results.values() if 'bars' in r)
    failed = len(SYMBOLS) - successful
    
    print(f"Successful: {successful}/{len(SYMBOLS)}")
    print(f"Failed: {failed}/{len(SYMBOLS)}")
    
    if successful > 0:
        total_bars = sum(r['bars'] for r in results.values() if 'bars' in r)
        print(f"Total bars fetched: {total_bars:,}")
        
        print("\nDetails:")
        for symbol, result in results.items():
            if 'bars' in result:
                print(f"  {symbol}: {result['bars']} bars ({result['start']} to {result['end']})")
            else:
                print(f"  {symbol}: ❌ {result.get('error', 'Unknown error')}")
    
    print("\n✅ Historical data fetch complete!")
    print(f"Files saved in: {os.path.abspath(DATA_DIR)}/")
    
    return results

if __name__ == "__main__":
    fetch_historical_data()
