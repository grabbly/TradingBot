# Sentiment-Based Trading Strategy

## Overview
Automated daily sentiment-driven trading strategy on Alpaca Paper Trading account.

**Start Date:** January 7, 2026  
**Initial Capital:** $100,000  
**Account Type:** Alpaca Paper Trading  
**Market:** US Equities

---

## Trading Universe

### Active Symbols (7)
- **AAPL** - Apple Inc.
- **AMZN** - Amazon.com Inc.
- **GOOGL** - Alphabet Inc.
- **META** - Meta Platforms Inc.
- **MSFT** - Microsoft Corporation
- **NVDA** - NVIDIA Corporation
- **TSLA** - Tesla Inc.

### Source
Tracked in PostgreSQL table `tracked_symbols` (active=true)

---

## Strategy Logic

### Core Principle
**Hold top-4 symbols by daily sentiment score**

### Daily Workflow

#### 1. News Collection (`news-collector`)
- **Schedule:** Every 4 hours
- **Source:** EODHD API
- **Action:** Fetch 10 latest articles per symbol
- **Storage:** PostgreSQL table `news_articles`
- **Deduplication:** Automatic via UNIQUE constraint on `article_id`

#### 2. Sentiment Analysis (`sentiment-analysis`)
- **Schedule:** 15:00 (3:00 PM) daily
- **Process:**
  - Read up to 10 unanalyzed articles per symbol (fetched today)
  - Send to OpenAI GPT-4 via AI Agent
  - Parse sentiment score (-1.0 to +1.0) and rationale
  - Store in `sentiment_scores` table
  - Mark articles as `analyzed=true`
- **Error Handling:** 
  - Retry on malformed AI response
  - Fallback to neutral score (0.0) on repeated failure

#### 3. Portfolio Execution (`sentiment-executor`)
- **Schedule:** 18:00 (6:00 PM) daily
- **Trading Days:** Monday-Friday only (Asia/Jerusalem timezone)
- **Decision Flow:**
  1. Get account info from Alpaca
  2. Fetch today's sentiment scores from DB
  3. Filter top-4 symbols by sentiment
  4. Get current open positions from Alpaca
  5. Calculate rebalancing actions
  6. Execute trades
  7. Log to database
  8. Send Telegram notifications

---

## Position Sizing

### Risk Management
- **Maximum per position:** $250
- **Portfolio composition:** Top-4 symbols, equal-weighted
- **Total exposure:** Up to $1,000 (4 × $250)

### Allocation Logic
```javascript
// Calculate budget from positions to close, or use available cash
totalBudget = positionsToClose.sum(market_value) || account.cash

// Split equally among new positions, capped at $250
valuePerSymbol = min(totalBudget / newSymbolsCount, 250)
```

### First-Run Behavior
- If portfolio is empty: use available cash
- Cap remains at $250 per symbol even with full $100k available
- Conservative approach: preserves capital, low risk

---

## Trade Execution

### Sell Orders
- **Type:** Market order (full position close)
- **Method:** DELETE `/v2/positions/{symbol}`
- **Trigger:** Symbol not in top-4 sentiment
- **Timing:** Immediate
- **Telegram Alert:** 🔴 SELL with symbol, value, reason

### Buy Orders
- **Type:** Market order (notional)
- **Trigger:** Symbol in top-4 but not currently held
- **Wait Period:** 10 seconds after sell orders complete
- **Notional Amount:** `$valuePerSymbol` (max $250)
- **Telegram Alert:** 🟢 BUY with symbol, value, reason

### Order Flow
```
positions_to_close 
  → Telegram_Sell_Alert 
  → Alpaca DELETE /positions/{symbol}

positions_to_open 
  → Telegram_Buy_Alert 
  → Wait 10s 
  → Alpaca POST /orders (notional buy)

merge → save to positions table → portfolio summary
```

---

## Database Schema

### Tables Used

#### `news_articles`
```sql
- id (PK)
- symbol
- article_id (UNIQUE)
- title, content, url, source
- published_at, fetched_at
- analyzed (boolean, default false)
```

#### `sentiment_scores`
```sql
- id (PK)
- date, symbol (UNIQUE together)
- sentiment_score (-1.0 to +1.0)
- rationale (text)
- article_count
```

#### `account_balance`
```sql
- id (PK)
- date (UNIQUE)
- balance (total equity)
- change (daily % change)
```

#### `positions`
```sql
- id (PK)
- date
- symbol
- order_type ('buy' or 'sell')
- value (USD)
- sentiment_score (optional)
- created_at
```

#### `tracked_symbols`
```sql
- id (PK)
- symbol (UNIQUE)
- name
- active (boolean)
```

---

## Telegram Notifications

### Chat ID
`<configured in workflow>`

### Message Types

#### 🔴 SELL ORDER
```
Symbol: GOOGL
Value: $250.50
Reason: Not in top-4 sentiment
Time: HH:mm:ss
```

#### 🟢 BUY ORDER
```
Symbol: TSLA
Value: $250.00
Reason: Top-4 sentiment
Time: HH:mm:ss
```

#### 📊 PORTFOLIO SUMMARY
```
Total Value: $100,123.45
Daily P/L: $123.45 (0.12%)
Cash: $99,000.00
Buying Power: $99,000.00
Time: HH:mm:ss
```

Sent after all trades complete.

---

## Credentials

### PostgreSQL
- **Host:** ***REMOVED***
- **Database:** trading_bot
- **User:** n8n_user
- **Password:** `<configured in n8n credentials>`
- **Access:** Mac (192.168.1.0/24) + n8n Docker (172.17.0.0/16)

### Alpaca Paper Trading
- **Base URL:** https://paper-api.alpaca.markets/v2
- **Auth:** HTTP Headers
  - `APCA-API-KEY-ID: <your-api-key-id>`
  - `APCA-API-SECRET-KEY: <your-api-secret-key>`

### OpenAI
- Used via n8n AI Agent node
- Model: GPT-4 (via OpenAI Chat Model)

### Telegram
- **Bot Token:** Configured in n8n credentials
- **Chat ID:** `<your-chat-id>`

---

## Workflow Schedule Summary

| Time  | Workflow | Action |
|-------|----------|--------|
| Every 4h | news-collector | Fetch news articles |
| 15:00 | sentiment-analysis | Analyze sentiment with AI |
| 18:00 | sentiment-executor | Execute trades |

**Note:** All times in server timezone (Asia/Jerusalem)

---

## Performance Tracking

### Metrics Logged
1. **Daily account balance** (equity, change %)
2. **All trades** (buy/sell, symbol, value, date)
3. **Sentiment scores** (per symbol, per day)
4. **News articles** (count per symbol)

### Viewing Data
- **PGAdmin:** http://localhost:5050 (Mac)
  - Email: admin@example.com
  - Password: admin123
- **SQL Queries:** Via SSH or PGAdmin

---

## Risk Parameters

### Current Settings
- **Max position size:** $250 per symbol
- **Max symbols:** 4 (top sentiment)
- **Total max exposure:** $1,000
- **Leverage:** None (cash account)
- **Stop loss:** None (daily rebalance only)
- **Profit target:** None (hold until sentiment changes)

### Capital Preservation
- **Initial:** $100,000
- **At risk:** ~1% ($1,000 / $100,000)
- **Reserve:** $99,000 in cash

**Rationale:** Conservative approach for testing; can scale up after validation.

---

## Execution Example

### Scenario: January 7, 2026

#### Morning (15:00) - Sentiment Analysis Results
```
TSLA:   0.85  (top-1)
MSFT:   0.80  (top-2)
NVDA:   0.80  (top-3)
AMZN:   0.75  (top-4)
------- cut -------
GOOGL:  0.40
META:   0.30
AAPL:   0.05
```

#### Current Portfolio (before 18:00)
```
MSFT:  $250
NVDA:  $250
AMZN:  $250
GOOGL: $250
```

#### Trade Decisions (18:00)
- **SELL:** GOOGL ($250) - not in top-4
- **BUY:** TSLA ($250) - in top-4, not held

#### Final Portfolio (after 18:00)
```
TSLA:  $250  (new)
MSFT:  $250  (held)
NVDA:  $250  (held)
AMZN:  $250  (held)
```

#### Database Entries
```sql
-- positions table
INSERT (date='2026-01-07', symbol='GOOGL', order_type='sell', value=250.00)
INSERT (date='2026-01-07', symbol='TSLA', order_type='buy', value=250.00)

-- account_balance table
INSERT (date='2026-01-07', balance=100001.14, change=0.000011)
```

---

## Maintenance & Monitoring

### Daily Checks
1. Verify workflows executed (check n8n logs)
2. Review Telegram messages
3. Confirm DB entries in `positions` table
4. Check account balance trend

### Weekly Checks
1. Review sentiment accuracy vs. price movement
2. Analyze which symbols most frequently in top-4
3. Check for stuck/failed workflows
4. Review error logs

### Adjustments
- **Increase position size:** Raise `maxPerSymbol` cap after validation
- **Add symbols:** Insert into `tracked_symbols` with `active=true`
- **Change schedule:** Edit workflow trigger times
- **Modify top-N:** Edit `filter_top_sentiment_score` (currently top-4)

---

## Files & Locations

### Workflows
- `/Users/gabby/git/TradingBot/n8n/workflows/news-collector.json`
- `/Users/gabby/git/TradingBot/n8n/workflows/sentiment-analysis.json`
- `/Users/gabby/git/TradingBot/n8n/workflows/sentiment-executor.json`

### Database Schema
- `/Users/gabby/git/TradingBot/db/sentiment_schema.sql`

### Documentation
- `/Users/gabby/git/TradingBot/README.md`
- `/Users/gabby/git/TradingBot/n8n/CREDENTIALS_SETUP.md`
- `/Users/gabby/git/TradingBot/STRATEGY.md` (this file)

---

## Version History

### v1.0 - January 7, 2026
- Initial implementation
- Conservative risk ($250 per position)
- Top-4 sentiment strategy
- Telegram alerts integrated
- PostgreSQL logging active

---

## Future Enhancements (Planned)

### Short Term
- [ ] Scale position sizes after 2-week validation
- [ ] Add sentiment trend analysis (3-day average)
- [ ] Implement trailing stop losses
- [ ] Add web dashboard for visualization

### Long Term
- [ ] Multi-timeframe sentiment (intraday + daily)
- [ ] Machine learning model for sentiment prediction
- [ ] Sector rotation based on aggregate sentiment
- [ ] Integration with technical indicators (EMA crossover)

---

**Last Updated:** January 7, 2026  
**Status:** Active  
**Next Review:** January 14, 2026
