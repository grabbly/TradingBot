# TradingBot Architecture

## Database Schema (PostgreSQL - trading_bot)

### EMA Strategy Tables
- **ema_snapshots** - Real-time EMA data (10 periods: 5,8,9,13,20,21,34,50,100,200)
- **trades** - Trade history for EMA strategy
- **bot_state** - Bot configuration and state
- **schema_migrations** - Database version control

### Sentiment Strategy Tables
- **news_articles** - News feed with deduplication (UNIQUE: article_id + symbol)
- **sentiment_scores** - Daily sentiment analysis (UNIQUE: date + symbol)
- **positions** - Trade history for sentiment strategy
- **account_balance** - Daily account balance tracking
- **tracked_symbols** - Active symbols for analysis (7 symbols: NVDA, AAPL, TSLA, GOOGL, MSFT, AMZN, META)

## N8N Workflows

### EMA Strategy (Real-time)
```
ema-logger.json (every 3 seconds)
  → Fetch market data (Alpaca)
  → Calculate 10 EMAs dynamically (5-200)
  → Insert into ema_snapshots

ema-crossover-bot.json
  → Detect EMA crossovers
  → Execute trades based on signals
```

### Sentiment Strategy (Daily)
```
news-collector.json (every 4 hours)
  → Get tracked_symbols (PostgreSQL)
  → Fetch news (EODHD API)
  → Insert with deduplication (ON CONFLICT DO NOTHING)

sentiment-analysis.json (15:00 daily)
  → Get_Active_Symbols (PostgreSQL)
  → Get_Unanalyzed_News (analyzed=false)
  → AI sentiment analysis (OpenAI)
  → save_sentiment_to_db (ON CONFLICT UPDATE)
  → mark_articles_analyzed (UPDATE analyzed=true)

sentiment-executor.json (18:00 daily)
  → Check weekday (Mon-Fri only)
  → Get account info (Alpaca)
  → save_account_balance (PostgreSQL)
  → get_sentiment_scores (today's scores)
  → filter_top_sentiment_score (top 4)
  → Compare with open positions
  → Execute trades: close non-top4, buy top4
  → save_positions_to_db (PostgreSQL)
```

## Key Features

### Database-Level Data Integrity
- **Deduplication**: UNIQUE constraints prevent duplicate news/sentiment
- **Transactions**: Atomic operations ensure data consistency
- **Indexes**: 11 indexes for fast queries on symbol, date, analyzed flag

### Graceful Degradation
- **EMA Logger**: Calculates only available EMAs based on bar count
  - 16 bars → 4 EMAs (5,8,9,13)
  - 250 bars → all 10 EMAs
- **Sentiment Analysis**: Skips symbols with no new articles

### Migration System
- Version-controlled schema changes in `/db/migrations/`
- Checksum tracking in `schema_migrations` table
- Manual application via postgres user (ownership requirements)

## Data Flow

### EMA Strategy
```
Market Data → EMA Calculation → PostgreSQL → Trading Signals → Alpaca
```

### Sentiment Strategy
```
EODHD API → news_articles → AI Analysis → sentiment_scores → Alpaca
                ↓                              ↓
           analyzed flag                  positions table
```

## Credentials (N8N)
- **postgres_trading_bot**: n8n_user / ***REMOVED***
- **httpCustomAuth**: Alpaca API authentication
- **openAiApi**: OpenAI API for sentiment analysis
- **httpQueryAuth**: EODHD API for news

## Server Info
- **Host**: ***REMOVED***:5432
- **Database**: trading_bot
- **Users**: postgres (owner), n8n_user (worker)
- **Sudo**: 2356HJK
