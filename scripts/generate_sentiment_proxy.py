#!/usr/bin/env python3
"""
Create Sentiment Proxy for Backtest (2023-2025)
Task 1.1.2 - Phase 1: Validation

Fetches historical news headlines and generates sentiment scores using FinBERT.
Creates sentiment proxy CSV for backtesting v1.0 strategy.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm
import time

# Load environment variables
load_dotenv()

# Configuration
SYMBOLS = ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA']
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)
DATA_DIR = 'data'
OUTPUT_FILE = f'{DATA_DIR}/sentiment_proxy_2023-2025.csv'

# EODHD API settings
EODHD_API_KEY = os.getenv('EODHD_API_KEY')
EODHD_BASE_URL = 'https://eodhistoricaldata.com/api/news'

# FinBERT model
FINBERT_MODEL = 'ProsusAI/finbert'

class SentimentAnalyzer:
    """FinBERT sentiment analyzer"""
    
    def __init__(self):
        print("Loading FinBERT model (ProsusAI/finbert)...")
        self.tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
        self.model.eval()
        print("✅ FinBERT loaded")
    
    def analyze(self, text):
        """
        Analyze sentiment of text
        Returns: sentiment score from -1 (negative) to +1 (positive)
        """
        try:
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Get probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT classes: positive, negative, neutral
            positive = probs[0][0].item()
            negative = probs[0][1].item()
            neutral = probs[0][2].item()
            
            # Convert to -1 to +1 scale
            sentiment = positive - negative
            
            return sentiment, positive, negative, neutral
        
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return 0.0, 0.0, 0.0, 1.0

def fetch_news_for_symbol(symbol, from_date, to_date, limit=50):
    """Fetch news headlines for a symbol from EODHD"""
    
    # Convert dates to timestamps
    from_ts = int(from_date.timestamp())
    to_ts = int(to_date.timestamp())
    
    params = {
        'api_token': EODHD_API_KEY,
        's': f'{symbol}.US',
        'limit': limit,
        'from': from_ts,
        'to': to_ts
    }
    
    try:
        response = requests.get(EODHD_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ❌ Error fetching news: {e}")
        return []

def generate_sentiment_proxy():
    """Generate sentiment proxy for all symbols and dates"""
    
    # Initialize FinBERT
    analyzer = SentimentAnalyzer()
    
    print(f"\n📰 Generating sentiment proxy for {len(SYMBOLS)} symbols")
    print(f"Period: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Model: {FINBERT_MODEL}")
    print("-" * 60)
    
    all_sentiments = []
    
    # Process each symbol
    for symbol in SYMBOLS:
        print(f"\n🔍 Processing {symbol}...")
        
        # Fetch news in chunks (EODHD has limits)
        # We'll fetch news for each quarter
        current_date = START_DATE
        symbol_sentiments = {}
        
        while current_date < END_DATE:
            chunk_end = min(current_date + timedelta(days=90), END_DATE)
            
            print(f"  Fetching news: {current_date.date()} to {chunk_end.date()}", end=' ')
            news = fetch_news_for_symbol(symbol, current_date, chunk_end, limit=100)
            print(f"({len(news)} articles)")
            
            # Analyze sentiment for each article
            for article in news:
                try:
                    # Get article date
                    article_date = datetime.fromtimestamp(article['date'])
                    date_key = article_date.date()
                    
                    # Analyze title (primary signal)
                    title = article.get('title', '')
                    if not title:
                        continue
                    
                    sentiment, pos, neg, neu = analyzer.analyze(title)
                    
                    # Aggregate by date
                    if date_key not in symbol_sentiments:
                        symbol_sentiments[date_key] = []
                    
                    symbol_sentiments[date_key].append({
                        'sentiment': sentiment,
                        'positive': pos,
                        'negative': neg,
                        'neutral': neu
                    })
                
                except Exception as e:
                    continue
            
            current_date = chunk_end
            time.sleep(0.5)  # Rate limiting
        
        # Calculate daily average sentiment
        print(f"  Calculating daily averages...")
        for date, sentiments in symbol_sentiments.items():
            avg_sentiment = sum(s['sentiment'] for s in sentiments) / len(sentiments)
            avg_positive = sum(s['positive'] for s in sentiments) / len(sentiments)
            avg_negative = sum(s['negative'] for s in sentiments) / len(sentiments)
            avg_neutral = sum(s['neutral'] for s in sentiments) / len(sentiments)
            
            all_sentiments.append({
                'date': date,
                'symbol': symbol,
                'sentiment': round(avg_sentiment, 4),
                'positive': round(avg_positive, 4),
                'negative': round(avg_negative, 4),
                'neutral': round(avg_neutral, 4),
                'article_count': len(sentiments)
            })
        
        print(f"  ✅ {len(symbol_sentiments)} days with sentiment data")
    
    # Create DataFrame
    df = pd.DataFrame(all_sentiments)
    df = df.sort_values(['date', 'symbol'])
    
    # Fill missing dates with neutral sentiment (0.0)
    # Create complete date range
    print(f"\n📅 Filling missing dates with neutral sentiment...")
    complete_data = []
    
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
    
    for symbol in SYMBOLS:
        symbol_df = df[df['symbol'] == symbol].set_index('date')
        
        for date in date_range:
            date_obj = date.date()
            
            if date_obj in symbol_df.index:
                # Use actual sentiment
                row = symbol_df.loc[date_obj]
                complete_data.append({
                    'date': date_obj,
                    'symbol': symbol,
                    'sentiment': row['sentiment'],
                    'positive': row['positive'],
                    'negative': row['negative'],
                    'neutral': row['neutral'],
                    'article_count': row['article_count']
                })
            else:
                # Use neutral sentiment
                complete_data.append({
                    'date': date_obj,
                    'symbol': symbol,
                    'sentiment': 0.0,
                    'positive': 0.0,
                    'negative': 0.0,
                    'neutral': 1.0,
                    'article_count': 0
                })
    
    df_complete = pd.DataFrame(complete_data)
    
    # Save to CSV
    df_complete.to_csv(OUTPUT_FILE, index=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(df_complete):,}")
    print(f"Date range: {df_complete['date'].min()} to {df_complete['date'].max()}")
    print(f"Symbols: {len(SYMBOLS)}")
    
    print(f"\nSentiment coverage:")
    for symbol in SYMBOLS:
        symbol_data = df_complete[df_complete['symbol'] == symbol]
        with_news = (symbol_data['article_count'] > 0).sum()
        total_days = len(symbol_data)
        coverage = (with_news / total_days) * 100
        print(f"  {symbol}: {with_news}/{total_days} days ({coverage:.1f}%) with news data")
    
    print(f"\nSentiment statistics:")
    print(df_complete[df_complete['article_count'] > 0]['sentiment'].describe())
    
    print(f"\n✅ Sentiment proxy saved to: {OUTPUT_FILE}")
    
    return df_complete

if __name__ == "__main__":
    print("=" * 60)
    print("SENTIMENT PROXY GENERATOR")
    print("Task 1.1.2 - Phase 1: Validation")
    print("=" * 60)
    
    # Check if output already exists
    if os.path.exists(OUTPUT_FILE):
        response = input(f"\n⚠️  {OUTPUT_FILE} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            exit(0)
    
    # Generate sentiment proxy
    df = generate_sentiment_proxy()
    
    print("\n🎉 Task 1.1.2 complete!")
    print(f"Next: Task 1.1.3 - Create backtest script")
