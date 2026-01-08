#!/usr/bin/env python3
"""
Create Sentiment Proxy for Backtest (2023-2025) - SIMPLIFIED VERSION
Task 1.1.2 - Phase 1: Validation

Generates baseline sentiment scores for backtesting v1.0 strategy.
Uses random/synthetic sentiment as proxy since we don't have historical news access.

Note: This is Phase 1 validation only. Phase 2 will add real FinBERT sentiment.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
SYMBOLS = ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA']
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)
DATA_DIR = 'data'
OUTPUT_FILE = f'{DATA_DIR}/sentiment_proxy_2023-2025.csv'

def generate_baseline_sentiment():
    """
    Generate baseline sentiment proxy for backtest validation
    
    Strategy: Semi-random sentiment with realistic patterns:
    - Mostly neutral (70% between -0.2 to +0.2)
    - Some positive bias for tech stocks (AAPL, MSFT, GOOGL, NVDA)
    - Occasional strong signals (10% outside -0.4 to +0.4)
    - Persistent trends (sentiment auto-correlates day-to-day)
    """
    
    print("=" * 60)
    print("BASELINE SENTIMENT PROXY GENERATOR")
    print("Task 1.1.2 - Phase 1: Validation (Simplified)")
    print("=" * 60)
    print(f"\n📊 Generating baseline sentiment for {len(SYMBOLS)} symbols")
    print(f"Period: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Method: Semi-random with realistic patterns")
    print("-" * 60)
    
    # Generate date range
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
    
    all_data = []
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    for symbol in SYMBOLS:
        print(f"\n🔍 Generating {symbol}...", end=' ')
        
        # Determine symbol bias (tech stocks slightly more positive)
        if symbol in ['AAPL', 'MSFT', 'GOOGL', 'NVDA']:
            bias = 0.05  # Slight positive bias for successful tech
        elif symbol == 'TSLA':
            bias = 0.0  # TSLA is volatile, no bias
        else:
            bias = 0.02  # Small positive bias for large caps
        
        # Generate sentiment with persistence (AR(1) model)
        sentiment_values = []
        prev_sentiment = bias
        
        for _ in date_range:
            # Sentiment auto-correlates (0.7 weight on previous day)
            noise = np.random.normal(0, 0.15)
            sentiment = 0.7 * prev_sentiment + 0.3 * (bias + noise)
            
            # Clip to reasonable range
            sentiment = np.clip(sentiment, -0.8, 0.8)
            
            sentiment_values.append(sentiment)
            prev_sentiment = sentiment
        
        # Add to dataset
        for date, sentiment in zip(date_range, sentiment_values):
            all_data.append({
                'date': date.date(),
                'symbol': symbol,
                'sentiment': round(sentiment, 4),
                'method': 'baseline'  # Mark as baseline for tracking
            })
        
        print(f"✅ {len(sentiment_values)} days")
        print(f"  Mean: {np.mean(sentiment_values):.4f}, Std: {np.std(sentiment_values):.4f}")
        print(f"  Range: [{min(sentiment_values):.4f}, {max(sentiment_values):.4f}]")
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(df):,}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    
    print(f"\nSentiment statistics:")
    print(df['sentiment'].describe())
    
    print(f"\n✅ Baseline sentiment proxy saved to: {OUTPUT_FILE}")
    print(f"\n📝 Note: This is synthetic data for Phase 1 validation")
    print(f"   Phase 2 will replace with real FinBERT sentiment from news")
    
    return df

if __name__ == "__main__":
    # Generate baseline sentiment
    df = generate_baseline_sentiment()
    
    print("\n🎉 Task 1.1.2 complete!")
    print(f"Next: Task 1.1.3 - Create backtest script")
