# Trading Strategy v1.0 - Sentiment-Based Rebalancing

**Status:** Active  
**Start Date:** January 7, 2026  
**Initial Capital:** $100,000

## Quick Links

- [Full Strategy Documentation](STRATEGY.md)
- [Execution Workflow](workflows/sentiment-executor.json)
- [Sentiment Analysis Workflow](workflows/sentiment-analysis.json)
- [News Collector Workflow](workflows/news-collector.json)

## Overview

Automated trading strategy that:
- Analyzes news sentiment daily for 7 tech stocks
- Holds top-4 stocks by sentiment score
- Rebalances portfolio daily at 18:00 (Mon-Fri)
- Max risk: $250 per position, $1,000 total

## Files

```
strategy_v1/
├── README.md                       # This file (quick overview)
├── STRATEGY.md                     # Complete strategy documentation
├── CREDENTIALS_SETUP.md            # n8n credentials configuration guide
├── workflows/                      # Production workflows
│   ├── news-collector.json         # Fetches news every 4 hours
│   ├── sentiment-analysis.json     # Analyzes sentiment at 15:00 daily
│   ├── sentiment-executor.json     # Executes trades at 18:00 daily
│   ├── ema-crossover-bot.json      # EMA crossover strategy (alternative)
│   └── ema-logger.json             # EMA data logging
└── archive/                        # Legacy/migration workflows
    ├── db-migrate.json
    ├── fix-permissions-and-migrate.json
    ├── change-owner-and-migrate.json
    └── apply-migration-001-manual.json
```

## Key Metrics

- **Universe:** 7 stocks (AAPL, AMZN, GOOGL, META, MSFT, NVDA, TSLA)
- **Position Size:** Max $250 per stock
- **Portfolio:** Hold top-4 by sentiment
- **Execution:** Daily at 18:00 (Asia/Jerusalem timezone)
- **Notifications:** Telegram alerts for all trades

## Workflows Schedule

1. **News Collection** - Every 4 hours
   - Fetches 10 latest articles per symbol
   - Stores in PostgreSQL `news_articles`

2. **Sentiment Analysis** - Daily 15:00
   - Analyzes unanalyzed news with GPT-4
   - Calculates sentiment scores (-1 to +1)
   - Updates `sentiment_scores` table

3. **Trade Execution** - Daily 18:00 (Mon-Fri)
   - Compares current positions with top-4 sentiment
   - Closes positions not in top-4
   - Opens positions for top-4 not held
   - Sends Telegram notifications

## Performance Tracking

Monitor via:
- PostgreSQL `positions` table (trade history)
- PostgreSQL `account_balance` table (daily equity)
- Telegram notifications (real-time alerts)
- [Treddy Dashboard](http://treddy.acebox.eu) (visual charts)

## Version History

- **v1.0** (2026-01-07) - Initial release
  - Sentiment-based top-4 strategy
  - $250 max per position
  - Telegram integration
  - Risk management implemented
