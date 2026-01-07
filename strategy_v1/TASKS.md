# v2.0 Upgrade Tasks - Actionable Checklist

**Created:** 2026-01-07  
**Sprint:** 8 weeks (Feb 2026)  
**Starting Capital:** $1,000 (paper → $500 real → $1,000 full)

---

## 🚨 Pre-Flight Checklist (Before Phase 1)

- [ ] Confirm Alpaca Paper Trading account active
- [ ] Verify PostgreSQL connection from Mac
- [ ] Check current v1.0 running status (is it live?)
- [ ] Backup current database: `pg_dump trading_bot > backup_v1_20260107.sql`
- [ ] Clone strategy_v1 → strategy_v2 folder structure
- [ ] Setup dev environment: Python venv with dependencies

**Time:** 2 hours

---

## 📊 Phase 1: Validation & Foundation (Weeks 1-2)

### Task 1.1: Backtest v1.0 Strategy ⭐ CRITICAL

**Goal:** Prove v1.0 works (or doesn't) with historical data

**Sub-tasks:**
- [ ] **1.1.1** Fetch historical data (2023-2025)
  - API: Alpaca `/v2/stocks/{symbol}/bars` with timeframe=1Day
  - Symbols: AAPL, AMZN, GOOGL, META, MSFT, NVDA, TSLA
  - Save to CSV: `data/historical_{symbol}_2023-2025.csv`
  - Script: `scripts/fetch_historical_data.py`
  - **Time:** 3 hours

- [ ] **1.1.2** Create sentiment proxy for backtest
  - **Decision:** Use FinBERT for historical sentiment analysis
  - Process:
    - Fetch historical news headlines for each symbol (EODHD API)
    - Run through FinBERT (ProsusAI/finbert) via HuggingFace API
    - Generate sentiment scores for 2023-2025 period
  - Store in: `data/sentiment_proxy_2023-2025.csv`
  - **Time:** 6 hours

- [ ] **1.1.3** Extend backtest script for sentiment
  - Base: `scripts/backtest_ema_strategy.py`
  - New: `scripts/backtest_sentiment_v1.py`
  - Logic:
    - Daily: Get sentiment scores, select top-4
    - Compare with current positions
    - Execute trades (market orders in simulation)
    - Track: equity, trades, Sharpe, drawdown
  - Output: Results table + equity curve plot
  - **Time:** 8 hours

- [ ] **1.1.4** Run backtest & analyze results
  - Scenarios: 2023 (bull), 2024 (mixed), 2025 (current)
  - Calculate: Total return, Sharpe, max DD, win rate
  - Compare vs. SPY buy-and-hold
  - **Decision point:** If Sharpe < 0.5 → STOP or pivot
  - **Time:** 2 hours

**Total Phase 1.1:** 15-19 hours (2 days)  
**Deliverable:** `reports/backtest_v1_results_20260107.md`

---

### Task 1.2: Analyze v1.0 Live Performance

**Goal:** If v1.0 is already running, check first week results

**Sub-tasks:**
- [ ] **1.2.1** Query positions table
  - SQL: `SELECT * FROM positions WHERE date >= '2026-01-07' ORDER BY date`
  - Count: wins vs. losses
  - Avg P&L per trade
  - **Time:** 30 min

- [ ] **1.2.2** Query sentiment stability
  - SQL: Top-4 symbols per day, check how often they change
  - Expected: < 2 changes/week (if stable)
  - **Time:** 30 min

- [ ] **1.2.3** Correlation analysis
  - Fetch: sentiment scores + next-day returns
  - Calculate Pearson correlation
  - Script: `scripts/analyze_sentiment_correlation.py`
  - **Time:** 2 hours

- [ ] **1.2.4** Visualize results
  - Matplotlib: Equity curve, trade distribution
  - Save: `reports/v1_live_week1_analysis.png`
  - **Time:** 1 hour

**Total Phase 1.2:** 4 hours  
**Condition:** Only if v1.0 running  
**Deliverable:** `reports/v1_live_analysis_20260107.md`

---

### Task 1.3: Cost Analysis

**Goal:** Calculate real costs vs. expected returns

**Sub-tasks:**
- [ ] **1.3.1** Calculate GPT-4 costs
  - Current: 7 symbols × 10 articles × 30 days = 2,100 requests/month
  - GPT-4 price: ~$0.03 per 1k tokens (input) + $0.06 per 1k tokens (output)
  - Estimate: ~1k tokens input, 200 tokens output per request
  - Monthly cost: 2,100 × (0.03 + 0.006) = ~$75.6
  - **Time:** 30 min

- [ ] **1.3.2** Estimate slippage
  - Assume: 0.1-0.2% slippage per market order
  - Daily trades: 2 (1 sell + 1 buy) × $250 = $500 volume
  - Monthly slippage: $500 × 0.15% × 20 days = ~$15
  - **Time:** 30 min

- [ ] **1.3.3** Opportunity cost
  - $1,000 capital at 5% annual (SPY) = $50/year = $4.17/month
  - v1.0 must beat $4.17/month to be worthwhile
  - **Time:** 15 min

- [ ] **1.3.4** Summary table
  - Total monthly cost: $75.6 (API) + $15 (slippage) = $90.6
  - Break-even: Need 9% monthly return just to cover costs (!)
  - **Conclusion:** Must reduce costs significantly
  - **Time:** 15 min

**Total Phase 1.3:** 1.5 hours  
**Deliverable:** `reports/cost_analysis_v1_20260107.md`  
**Critical Insight:** This proves GPT-4 too expensive for small account

---

## 🧠 Phase 2: Sentiment Upgrade (Weeks 3-4)

### Task 2.1: Replace GPT-4 with FinBERT

**Goal:** Cut sentiment analysis cost by 80%+

**Sub-tasks:**
- [ ] **2.1.1** Setup FinBERT model
  - **Decision:** Use `ProsusAI/finbert` (classical FinBERT model)
  - Model details:
    - Fine-tuned on financial news corpus
    - Output: 3 classes (positive, negative, neutral) + softmax scores
    - Convert to -1 to +1 scale for compatibility
  - Test on HuggingFace inference API
  - **Time:** 1.5 hours

- [ ] **2.1.2** Setup HuggingFace Inference API
  - Create account (free tier: 30k requests/month)
  - Get API token
  - Test endpoint: `POST https://api-inference.huggingface.co/models/{model}`
  - **Time:** 1 hour

- [ ] **2.1.3** Create new workflow: sentiment-analysis-v2.json
  - Clone: sentiment-analysis.json → sentiment-analysis-v2.json
  - Replace AI Agent node with HTTP Request to HF API
  - Input: article text (title + content)
  - Output: sentiment score (-1 to +1) + label
  - **Time:** 3 hours

- [ ] **2.1.4** Test on sample dataset
  - Collect 100 recent articles
  - Run through GPT-4 (baseline)
  - Run through FinBERT
  - Compare: accuracy, agreement rate
  - **Acceptance:** Agreement > 70%
  - **Time:** 3 hours

- [ ] **2.1.5** Calculate new costs
  - HuggingFace free tier: $0
  - Paid tier (if needed): $9/month for 100k requests
  - Savings: $75.6 → $0-9 (90% reduction)
  - **Time:** 30 min

**Total Phase 2.1:** 9.5 hours (1.5 days)  
**Deliverable:** `strategy_v2/workflows/sentiment-analysis-v2.json`  
**Question:** Use free tier or paid? Start free, upgrade if rate limited?

---

### Task 2.2: Expand Data Sources

**Goal:** 50+ data points per symbol/day (vs. current 10)

**Sub-tasks:**
- [ ] **2.2.1** Reddit API Integration
  - **Setup:**
    - Create Reddit app: https://www.reddit.com/prefs/apps
    - Get client_id, client_secret
    - OAuth flow for authentication
  - **Endpoints:**
    - Search: `/r/wallstreetbets/search.json?q={symbol}`
    - Hot posts: `/r/stocks/hot.json`
  - **Data:** Post title, body, score, comments count
  - **Frequency:** Every 4 hours (same as news)
  - **n8n:** HTTP Request node with OAuth2
  - **Storage:** `reddit_mentions` table in PostgreSQL
  - **Time:** 6 hours

- [ ] **2.2.2** Expand NewsAPI Coverage (DEFERRED)
  - **Decision:** Tight budget - focus on existing EODHD NewsAPI
  - **Alternative approach:**
    - Increase news fetch frequency: 4h → 2h
    - Add more article sources if available
    - Or limit to top 5-10 symbols instead of 22
  - **Social media (Twitter/X):** Defer to Phase 6 or later
  - **Time:** 2 hours (minor optimization)
  - **Note:** This task is optional for v2.0 MVP

- [ ] **2.2.3** StockTwits API Integration (DEFERRED)
  - **Decision:** Defer to later phase
  - **Reason:** Focus on core functionality first, add social signals after validation
  - **Future:** Add in Phase 6 if v2.0 shows consistent profitability
  - **Time:** 0 hours (skipped for now)

- [ ] **2.2.4** Create aggregation workflow
  - New workflow: `sentiment-aggregator-v2.json`
  - Runs: Daily at 14:00 (before analysis at 15:00)
  - Logic:
    - Fetch news from EODHD API
    - Fetch Reddit data (if implemented)
    - Weight: news 70%, reddit 30% (if available, otherwise 100% news)
    - Calculate weighted average sentiment per symbol
    - Store in: `sentiment_scores_v2` table
  - **Time:** 3 hours

- [ ] **2.2.5** Database schema updates
  - Create tables:
    ```sql
    CREATE TABLE reddit_mentions (
      id SERIAL PRIMARY KEY,
      symbol VARCHAR(10),
      post_id VARCHAR(50) UNIQUE,
      title TEXT,
      body TEXT,
      score INT,
      comments INT,
      created_at TIMESTAMP,
      fetched_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE TABLE sentiment_scores_v2 (
      id SERIAL PRIMARY KEY,
      date DATE,
      symbol VARCHAR(10),
      news_sentiment DECIMAL(5,4),
      reddit_sentiment DECIMAL(5,4),
      weighted_sentiment DECIMAL(5,4),
      total_mentions INT,
      UNIQUE(date, symbol)
    );
    ```
  - **Note:** Twitter/StockTwits tables deferred to later phase
  - **Time:** 45 minutes

**Total Phase 2.2:** 11.75 hours (1.5 days)  
**Deliverable:** 
- `strategy_v2/workflows/sentiment-aggregator-v2.json`
- `db/schema_v2_sentiment_sources.sql`

**Decision:** Focus on NewsAPI + Reddit only, defer social media to later

---

### Task 2.3: Sentiment Smoothing & Trend

**Goal:** Reduce whipsaws with moving average

**Sub-tasks:**
- [ ] **2.3.1** Modify sentiment_scores_v2 table
  - Add columns:
    - `ma3_sentiment` (3-day MA)
    - `ma7_sentiment` (7-day MA)
    - `trend` (up/down/flat based on MA slope)
  - **Time:** 30 min

- [ ] **2.3.2** Create MA calculation function
  - SQL function or Code node in n8n
  - Calculate MA3 from last 3 days sentiment
  - Update daily after sentiment analysis
  - **Time:** 2 hours

- [ ] **2.3.3** Update executor workflow
  - Use `ma3_sentiment` instead of raw `weighted_sentiment` for top-4 selection
  - **Time:** 1 hour

- [ ] **2.3.4** Backtest with smoothing
  - Re-run backtest with MA3 vs. raw sentiment
  - Compare: top-4 stability, number of trades, performance
  - **Acceptance:** < 2 changes/week in top-4
  - **Time:** 2 hours

**Total Phase 2.3:** 5.5 hours  
**Deliverable:** Updated `sentiment-executor-v2.json`

---

### Task 2.4: Enhanced Error Handling

**Goal:** Robust fallback when APIs fail

**Sub-tasks:**
- [ ] **2.4.1** Add retry logic to all API nodes
  - n8n: Use "Retry On Fail" settings
  - Exponential backoff: 1s, 2s, 4s, 8s
  - Max retries: 3
  - **Time:** 1 hour

- [ ] **2.4.2** Implement fallback sentiment
  - If sentiment analysis fails:
    - Use previous day's sentiment (not 0.0)
    - Mark as `fallback=true` in database
  - **Time:** 2 hours

- [ ] **2.4.3** Add Telegram alerts for failures
  - Alert when:
    - API quota exceeded
    - Sentiment analysis fails 3+ times
    - No data for 24+ hours
  - **Time:** 1 hour

**Total Phase 2.4:** 4 hours  
**Deliverable:** Robust workflows with error handling

---

## 📈 Phase 3: Technical Analysis Integration (Weeks 5-6)

### Task 3.1: EMA Filter (200-day Bull Bias)

**Goal:** Only trade stocks above 200 EMA

**Sub-tasks:**
- [ ] **3.1.1** Fetch historical data for EMA calculation
  - Need 300+ days of data per symbol (for 200 EMA)
  - Store in: `daily_bars` table
  - **Time:** 2 hours

- [ ] **3.1.2** Calculate EMA200 daily
  - Create: `calculate_ema.py` utility
  - Formula: EMA = Price × multiplier + EMA_prev × (1 - multiplier)
  - Multiplier = 2 / (period + 1) = 2 / 201 = 0.00995
  - Store in: `technical_indicators` table
  - **Time:** 3 hours

- [ ] **3.1.3** Add EMA filter to executor
  - Before selecting top-4:
    - Filter `sentiment_scores_v2` WHERE `price > ema200`
  - Only trade filtered symbols
  - **Time:** 2 hours

- [ ] **3.1.4** Backtest with EMA filter
  - Compare: v1 vs. v2 with EMA filter
  - Expected: Lower drawdown, less false entries
  - **Time:** 2 hours

**Total Phase 3.1:** 9 hours  
**Deliverable:** `technical_indicators` table + EMA filter logic

---

### Task 3.2: Entry Timing with EMA Crossovers

**Goal:** Use EMA 9/21 for better entry timing

**Sub-tasks:**
- [ ] **3.2.1** Calculate EMA9 and EMA21 daily
  - Add to `technical_indicators` table
  - **Time:** 1 hour

- [ ] **3.2.2** Detect crossovers
  - Bullish: EMA9 crosses above EMA21
  - Bearish: EMA9 crosses below EMA21
  - Store: `crossover` column (bullish/bearish/none)
  - **Time:** 2 hours

- [ ] **3.2.3** Update executor logic
  - Buy only if:
    - In top-4 sentiment
    - Price > EMA200
    - EMA9 > EMA21 (bullish)
  - Sell if:
    - Out of top-4 OR
    - EMA9 < EMA21 (bearish)
  - **Time:** 3 hours

- [ ] **3.2.4** Backtest with crossovers
  - Expected: Higher win rate, better timing
  - **Time:** 2 hours

**Total Phase 3.2:** 8 hours  
**Deliverable:** EMA crossover logic in executor

---

### Task 3.3: Volume & Momentum Filters

**Goal:** Add RSI and Volume confirmation

**Sub-tasks:**
- [ ] **3.3.1** Calculate RSI (14-day)
  - Formula: RSI = 100 - (100 / (1 + RS))
  - RS = Average Gain / Average Loss over 14 days
  - Library: Use `ta-lib` or pure Python/JS
  - Store in `technical_indicators`
  - **Time:** 3 hours

- [ ] **3.3.2** Calculate 20-day volume MA
  - Simple average of volume over 20 days
  - **Time:** 1 hour

- [ ] **3.3.3** Add filters to executor
  - Buy only if:
    - RSI < 70 (not overbought)
    - Volume > 20-day MA (confirmation)
  - **Time:** 2 hours

- [ ] **3.3.4** Backtest with filters
  - Expected: Reduced false entries, lower drawdown
  - **Time:** 2 hours

**Total Phase 3.3:** 8 hours  
**Deliverable:** RSI + Volume filters

---

### Task 3.4: Macro Event Filter

**Goal:** Skip trades before earnings/FOMC

**Sub-tasks:**
- [ ] **3.4.1** Fetch earnings calendar
  - API: Alpaca `/v1beta1/corporate-actions` or FMP
  - Store next earnings date per symbol
  - **Time:** 2 hours

- [ ] **3.4.2** Hardcode FOMC dates
  - 2026 FOMC schedule (8 meetings/year)
  - Store in config or database
  - **Time:** 30 min

- [ ] **3.4.3** Add skip logic to executor
  - If today or tomorrow is earnings → skip that symbol
  - If today ± 1 day is FOMC → skip all trades
  - **Time:** 2 hours

**Total Phase 3.4:** 4.5 hours  
**Deliverable:** Event-aware executor

---

## 💰 Phase 4: Risk Management Overhaul (Week 7)

### Task 4.1: Percentage-Based Position Sizing

**Goal:** 1% risk per trade, auto-scaling

**Sub-tasks:**
- [ ] **4.1.1** Get account balance from Alpaca
  - API: `GET /v2/account` → `equity` field
  - Run at start of executor workflow
  - **Time:** 30 min

- [ ] **4.1.2** Calculate position size per trade
  - Formula:
    ```
    risk_per_trade = equity × 0.01  # 1% risk
    sl_distance = entry_price - sl_price
    position_size_shares = risk_per_trade / sl_distance
    position_value = position_size_shares × entry_price
    ```
  - **Example:**
    - Equity: $1,000
    - Risk: $10
    - Entry: $100, SL: $95 → $5 risk/share
    - Shares: $10 / $5 = 2 shares
    - Position value: $200
  - **Time:** 2 hours

- [ ] **4.1.3** Implement in Code node
  - Input: account equity, entry price, sl price
  - Output: notional (position value in $)
  - **Time:** 2 hours

- [ ] **4.1.4** Test with fractional shares
  - Alpaca supports fractional shares
  - Order type: `notional` instead of `qty`
  - **Time:** 1 hour

**Total Phase 4.1:** 5.5 hours  
**Deliverable:** Dynamic position sizing

---

### Task 4.2: Stop-Loss & Take-Profit (MANDATORY)

**Goal:** Every trade must have SL/TP

**Sub-tasks:**
- [ ] **4.2.1** Research Alpaca bracket orders & calculate ATR
  - **Part A: ATR Calculation**
    - Add ATR14 to `technical_indicators` table
    - Calculate daily: TR = max(H-L, |H-C_prev|, |L-C_prev|)
    - ATR14 = 14-day MA of TR
    - Store for use in SL/TP calculation
  - **Part B: Bracket Orders**
    - API: `POST /v2/orders` with `order_class: bracket`
    - Parameters:
      - `side: buy/sell`
      - `notional: $200` (position size)
      - `stop_loss: {stop_price: entry - 2×ATR}`
      - `take_profit: {limit_price: entry + 4×ATR}`
  - **Time:** 3 hours

- [ ] **4.2.2** Calculate SL/TP prices (ATR-based)
  - **Decision:** Use ATR (Average True Range) for adaptive SL
  - **SL Formula:** Entry - (2 × ATR14)
  - **TP Formula:** Entry + (4 × ATR14)  [maintains 2:1 R:R]
  - **ATR Calculation:** 14-day average of: max(high-low, abs(high-prev_close), abs(low-prev_close))
  - **Example (low volatility stock):**
    - Entry: $100, ATR14: $1.50
    - SL: $100 - (2 × $1.50) = $97
    - TP: $100 + (4 × $1.50) = $106
  - **Example (high volatility tech stock):**
    - Entry: $100, ATR14: $3.00
    - SL: $100 - (2 × $3.00) = $94
    - TP: $100 + (4 × $3.00) = $112
  - **Time:** 2 hours (includes ATR calculation)

- [ ] **4.2.3** Update buy/sell nodes
  - Replace simple market orders with bracket orders
  - Include SL/TP in every order
  - **Time:** 3 hours

- [ ] **4.2.4** Test bracket orders on paper
  - Place test order
  - Verify SL/TP created automatically
  - **Time:** 1 hour

**Total Phase 4.2:** 8 hours  
**Deliverable:** All orders have ATR-based SL/TP

**Decision:** ATR-based adaptive SL (better for volatile tech stocks)

---

### Task 4.3: Portfolio Drawdown Limit

**Goal:** Pause trading if losses exceed 10%

**Sub-tasks:**
- [ ] **4.3.1** Track peak equity
  - Store: `peak_equity` in account_balance table
  - Update daily with max(current_equity, peak_equity)
  - **Time:** 1 hour

- [ ] **4.3.2** Calculate current drawdown
  - Formula: `drawdown = (peak_equity - current_equity) / peak_equity`
  - **Time:** 30 min

- [ ] **4.3.3** Add pause logic to executor
  - Before trading, check if `drawdown > 0.10` (10%)
  - If true: Skip all trades, send Telegram alert
  - Resume after manual review
  - **Time:** 2 hours

**Total Phase 4.3:** 3.5 hours  
**Deliverable:** Drawdown protection

---

### Task 4.4: Sector Diversification

**Goal:** Expand to 20-30 symbols across sectors

**Sub-tasks:**
- [ ] **4.4.1** Add new symbols to tracked_symbols
  - **Current (7):** AAPL, AMZN, GOOGL, META, MSFT, NVDA, TSLA
  - **Add (15):**
    - Tech: AMD, INTC, ORCL
    - Energy: XOM, CVX, COP
    - Healthcare: JNJ, UNH, PFE
    - Finance: JPM, BAC, WFC
    - Consumer: WMT, PG, KO
  - Total: 22 symbols
  - **Time:** 1 hour

- [ ] **4.4.2** Add sector mapping
  - New column: `sector` in tracked_symbols
  - Values: Tech, Energy, Healthcare, Finance, Consumer
  - **Time:** 30 min

- [ ] **4.4.3** Update top-4 selection logic
  - Constraint: Max 2 symbols from same sector
  - **Example:** If top sentiment is 3× Tech + 1× Energy, exclude lowest Tech
  - **Time:** 2 hours

- [ ] **4.4.4** Backtest with diversification
  - Calculate portfolio correlation
  - Target: < 0.6 (vs. current 0.85)
  - **Time:** 2 hours

**Total Phase 4.4:** 5.5 hours  
**Deliverable:** Diversified portfolio

---

## 🎛️ Phase 5: Operational Excellence (Week 8)

### Task 5.1: Real-Time Dashboard

**Goal:** Monitor performance visually

**Sub-tasks:**
- [ ] **5.1.1** Design dashboard layout
  - **Decision:** Extend Treddy Flask app (simple, informative)
  - **Requirements:**
    - Don't prioritize aesthetics/UX - focus on data visibility
    - Key metrics at a glance
    - Fast to implement
  - **Layout:** Single page with 4 sections (metrics, positions, equity, allocation)
  - **Time:** 1 hour

- [ ] **5.1.2** Add metrics endpoints
  - `/api/metrics`: Daily P&L, Sharpe, win rate
  - `/api/positions`: Current positions
  - `/api/equity-curve`: Historical equity
  - **Time:** 4 hours

- [ ] **5.1.3** Create frontend charts
  - Chart.js or Plotly
  - Charts:
    - Equity curve (line)
    - Daily P&L (bar)
    - Win/loss distribution (pie)
    - Sector allocation (donut)
  - **Time:** 6 hours

- [ ] **5.1.4** Add real-time updates
  - WebSocket or polling every 60s
  - **Time:** 2 hours

**Total Phase 5.1:** 13 hours (2 days)  
**Deliverable:** Live dashboard at http://treddy.acebox.eu

---

### Task 5.2: Advanced Alerting

**Goal:** Telegram alerts for anomalies

**Sub-tasks:**
- [ ] **5.2.1** Add alert for extreme sentiment
  - Trigger: Any symbol sentiment < -0.5 or > 0.8
  - Message: "⚠️ Extreme sentiment: {symbol} = {score}"
  - **Time:** 1 hour

- [ ] **5.2.2** Add alert for position loss
  - Trigger: Any position loss > 3% (approaching SL)
  - Check: Every hour during market hours
  - **Time:** 2 hours

- [ ] **5.2.3** Add alert for API failures
  - Trigger: Sentiment analysis fails 3+ times
  - Includes: Error message, stack trace
  - **Time:** 1 hour

**Total Phase 5.2:** 4 hours  
**Deliverable:** Smart Telegram alerts

---

### Task 5.3: A/B Testing Framework

**Goal:** Run v1.0 vs. v2.0 parallel

**Sub-tasks:**
- [ ] **5.3.1** Setup dual workflows
  - v1.0: sentiment-executor.json (existing)
  - v2.0: sentiment-executor-v2.json (new)
  - Both run daily, different accounts
  - **Time:** 2 hours

- [ ] **5.3.2** Create comparison report
  - Query both `positions` tables
  - Calculate: Return, Sharpe, win rate for each
  - Weekly comparison email/Telegram
  - **Time:** 3 hours

- [ ] **5.3.3** Run for 4 weeks
  - Monitor results
  - Statistical test: t-test for significance
  - **Decision:** Switch to winner after 4 weeks
  - **Time:** Ongoing

**Total Phase 5.3:** 5 hours setup + 4 weeks monitoring  
**Deliverable:** A/B test results

---

### Task 5.4: Automated Backtesting Pipeline

**Goal:** Weekly re-backtest to detect degradation

**Sub-tasks:**
- [ ] **5.4.1** Create cron job
  - Schedule: Every Sunday 00:00
  - Script: `scripts/weekly_backtest.sh`
  - **Time:** 1 hour

- [ ] **5.4.2** Automate backtest run
  - Fetch last 3 months data
  - Re-run strategy
  - Generate report
  - **Time:** 2 hours

- [ ] **5.4.3** Email report
  - If Sharpe drops > 20% → alert
  - Attach: Results PDF
  - **Time:** 2 hours

**Total Phase 5.4:** 5 hours  
**Deliverable:** Automated backtest pipeline

---

## 🚀 Phase 6: ML & Optimization (Optional - Month 3+)

**Note:** Only if v2.0 shows consistent profit for 3+ months

### Task 6.1: Custom Sentiment Model (Advanced)

**Goal:** Train model on our specific data

**Sub-tasks:**
- [ ] Collect 6 months sentiment + returns data
- [ ] Label dataset (positive/negative outcomes)
- [ ] Train PyTorch/TensorFlow model
- [ ] Deploy to HuggingFace or local server
- [ ] Integrate into workflow

**Effort:** 2 weeks  
**Deliverable:** Custom model with higher accuracy

---

### Task 6.2: Reinforcement Learning Portfolio (Advanced)

**Goal:** Optimize position sizing with RL

**Sub-tasks:**
- [ ] Setup Stable-Baselines3 environment
- [ ] Define state: sentiment, technicals, portfolio
- [ ] Define action: position size per symbol
- [ ] Define reward: Sharpe ratio
- [ ] Train PPO agent
- [ ] Backtest RL policy

**Effort:** 3 weeks  
**Deliverable:** RL-optimized position sizing

---

## 📅 Timeline Summary

| Week | Phase | Hours | Status |
|------|-------|-------|--------|
| 1-2 | Phase 1: Validation | 20-24h | 🔴 Not Started |
| 3-4 | Phase 2: Sentiment | 28-32h | 🔴 Not Started |
| 5-6 | Phase 3: Technical | 29-30h | 🔴 Not Started |
| 7 | Phase 4: Risk Mgmt | 22-23h | 🔴 Not Started |
| 8 | Phase 5: Operations | 27h | 🔴 Not Started |
| 9+ | Phase 6: ML (opt) | 80h+ | 🔴 Future |

**Total Core v2.0:** 126-136 hours (~4-5 hours/day for 8 weeks)
**Savings from decisions:** 6-7 hours (removed Twitter, StockTwits; optimized tasks)

---

## ✅ Decisions Made (2026-01-07)

1. **Task 1.1.2:** ✅ Use FinBERT for historical sentiment backtest (not random)
2. **Task 2.1.1:** ✅ ProsusAI/finbert (classical model)
3. **Task 2.2.2:** ✅ Skip Twitter/X - tight budget, focus on NewsAPI, or limit to 5-10 stocks
4. **Task 2.2.3:** ✅ StockTwits deferred to Phase 6 or later
5. **Task 4.2.2:** ✅ ATR-based adaptive SL (better for volatile tech stocks)
6. **Task 5.1.1:** ✅ Simple informative dashboard in Treddy Flask app

**Next Actions:** Create strategy_v2/ folder, start Phase 1

---

## 🎯 Success Criteria

**After Phase 1 (Week 2):**
- [ ] Backtest Sharpe ratio > 0.5
- [ ] Decision: Continue or pivot

**After Phase 2 (Week 4):**
- [ ] Sentiment cost < $10/month (vs. $75 currently)
- [ ] 50+ data points per symbol/day

**After Phase 3 (Week 6):**
- [ ] Backtest Sharpe > 0.8 with technical filters
- [ ] Max drawdown < 20%

**After Phase 4 (Week 7):**
- [ ] Every trade has SL/TP
- [ ] Position sizing adapts to account size
- [ ] Portfolio correlation < 0.6

**After Phase 5 (Week 8):**
- [ ] Dashboard live and updating
- [ ] v2.0 ready for paper trading
- [ ] Begin 4-week paper trading period

**After Paper Trading (Week 12):**
- [ ] If profitable: Deploy $500 real
- [ ] If loss: Debug and retry

---

## 📝 Next Immediate Actions

1. [ ] Answer open questions above
2. [ ] Create `strategy_v2/` folder structure
3. [ ] Setup Python venv with dependencies
4. [ ] Start Task 1.1.1: Fetch historical data
5. [ ] Commit this task list to git

**Start Date:** 2026-01-08 (tomorrow)  
**First Milestone:** Phase 1 complete by 2026-01-22
