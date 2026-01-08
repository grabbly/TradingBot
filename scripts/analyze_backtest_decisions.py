#!/usr/bin/env python3
"""
Analyze backtest decision-making logic
Show specific examples of how top-4 symbols were selected
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / 'data'

def analyze_decisions():
    """Show decision-making examples"""
    
    # Load sentiment data
    sentiment = pd.read_csv(DATA_DIR / 'sentiment_proxy_2023-2025.csv')
    sentiment['date'] = pd.to_datetime(sentiment['date'])
    
    # Analyze a few specific days
    example_dates = [
        '2023-01-03',  # First trading day
        '2023-06-15',  # Mid 2023
        '2024-01-15',  # Start 2024
        '2025-06-15',  # Mid 2025
        '2025-12-29',  # Last trading day
    ]
    
    print("="*80)
    print("🔍 BACKTEST DECISION-MAKING ANALYSIS")
    print("="*80)
    print("\nStrategy: Select TOP-4 symbols by sentiment score\n")
    
    for date_str in example_dates:
        date = pd.to_datetime(date_str)
        day_sentiment = sentiment[sentiment['date'] == date].copy()
        
        if len(day_sentiment) == 0:
            continue
        
        # Sort by sentiment (high to low)
        day_sentiment = day_sentiment.sort_values('sentiment', ascending=False)
        
        print(f"\n{'='*80}")
        print(f"📅 Date: {date_str}")
        print(f"{'='*80}\n")
        
        print(f"{'Rank':<6} {'Symbol':<8} {'Sentiment':<12} {'Selected'}")
        print("-" * 50)
        
        for i, (_, row) in enumerate(day_sentiment.iterrows(), 1):
            selected = "✅ BUY" if i <= 4 else "❌ SKIP"
            print(f"{i:<6} {row['symbol']:<8} {row['sentiment']:>10.4f}  {selected}")
        
        # Show decision summary
        top_4 = day_sentiment.head(4)['symbol'].tolist()
        print(f"\n💼 Portfolio: {', '.join(top_4)}")
        print(f"📊 Sentiment Range: {day_sentiment['sentiment'].min():.4f} to {day_sentiment['sentiment'].max():.4f}")
    
    # Analyze rebalancing frequency
    print(f"\n\n{'='*80}")
    print("📊 REBALANCING FREQUENCY ANALYSIS")
    print(f"{'='*80}\n")
    
    # Get top-4 for each day
    all_dates = sorted(sentiment['date'].unique())
    
    rebalance_count = 0
    prev_portfolio = None
    
    for date in all_dates:
        day_sentiment = sentiment[sentiment['date'] == date]
        if len(day_sentiment) == 0:
            continue
        
        current_portfolio = set(day_sentiment.nlargest(4, 'sentiment')['symbol'].tolist())
        
        if prev_portfolio is not None:
            if current_portfolio != prev_portfolio:
                rebalance_count += 1
        
        prev_portfolio = current_portfolio
    
    total_days = len(all_dates)
    rebalance_pct = (rebalance_count / total_days) * 100
    
    print(f"Total Trading Days: {total_days}")
    print(f"Rebalances: {rebalance_count}")
    print(f"Rebalance Frequency: {rebalance_pct:.1f}% of days")
    print(f"Avg Days Between Rebalances: {total_days / rebalance_count:.1f}")
    
    # Symbol popularity
    print(f"\n\n{'='*80}")
    print("📈 SYMBOL SELECTION FREQUENCY")
    print(f"{'='*80}\n")
    
    symbol_days = {}
    for date in all_dates:
        day_sentiment = sentiment[sentiment['date'] == date]
        if len(day_sentiment) == 0:
            continue
        
        top_4 = day_sentiment.nlargest(4, 'sentiment')['symbol'].tolist()
        for symbol in top_4:
            symbol_days[symbol] = symbol_days.get(symbol, 0) + 1
    
    # Sort by frequency
    sorted_symbols = sorted(symbol_days.items(), key=lambda x: x[1], reverse=True)
    
    print(f"{'Symbol':<10} {'Days in Portfolio':<20} {'Percentage':<15} {'Avg per Year'}")
    print("-" * 70)
    
    for symbol, days in sorted_symbols:
        pct = (days / total_days) * 100
        days_per_year = days / 3  # 3 years of data
        print(f"{symbol:<10} {days:<20} {pct:>6.1f}%          {days_per_year:>6.0f}")
    
    print(f"\n💡 Note: Portfolio always holds exactly 4 symbols (equal weight 25% each)")


if __name__ == '__main__':
    analyze_decisions()
