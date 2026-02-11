# Workflow Execution Sequence

## Daily Trading Cycle (Correct Order)

### 1️⃣ **News Collector** (Every 4 hours)
```
Schedule: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
Action: Fetch latest articles per symbol
Output: → PostgreSQL news_articles table
```

### 2️⃣ **EMA Logger (Data Collection)** (Daily background)
```
Schedule: Continuous or hourly during market hours
Action: Collect EMA indicators for technical analysis
Output: → PostgreSQL ema_snapshots table
Note: Supports the technical side (crossover detection)
```

### 3️⃣ **Sentiment Analysis** (15:00 UTC daily)
```
Schedule: 3:00 PM daily
Input: Unanalyzed articles from news_articles table
Action: Process with FinBERT (or GPT-4)
Output: → PostgreSQL sentiment_scores table
Wait: Before step 4 (needs sentiment ready)
```

### 4️⃣ **Sentiment Strategy Executor** (18:00 UTC daily)
```
Schedule: 6:00 PM daily
Input: sentiment_scores + EMA data + current positions
Action: 
  1. Get top-4 symbols by sentiment
  2. Check EMA crossover signals (technical filter)
  3. Calculate rebalancing
  4. Execute Alpaca trades
Output: → Alpaca orders + Telegram notifications
```

### 5️⃣ **EMA Crossover Bot** (Real-time monitoring)
```
Schedule: During market hours (09:30-16:00 EST)
Action: Monitor EMA cross signals in real-time
Output: → Alert/execute if crossover detected
Note: Supplement to daily Sentiment Strategy Executor
```

---

## Parallel vs Sequential

```
NEWS COLLECTOR (every 4h) ──┐
                             ├──→ SENTIMENT ANALYSIS (15:00) ──┐
EMA LOGGER (continuous) ────┤                                 ├──→ SENTIMENT EXECUTOR (18:00)
                             └────────────────────────────────┘

EMA CROSSOVER BOT (9:30-16:00 EST, real-time, independent)
```

---

## Correct Startup Sequence

### Day 1 Setup:
1. Start **News Collector** (will run 00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
2. Start **EMA Logger** (continuous background data)
3. Wait until 15:00 UTC → Run **Sentiment Analysis**
4. Wait until 18:00 UTC → Run **Sentiment Strategy Executor** (first trades)
5. Optionally enable **EMA Crossover Bot** for intraday signals

### Daily Cycle (after Day 1):
```
00:00 ← News Collector runs
04:00 ← News Collector runs  
08:00 ← News Collector runs
12:00 ← News Collector runs
15:00 ← Sentiment Analysis runs
16:00 ← News Collector runs
18:00 ← Sentiment Strategy Executor runs (makes trades)
20:00 ← News Collector runs

During 09:30-16:00 EST: EMA Crossover Bot monitors
```

---

## Implementation Checklist

- [ ] Activate **News Collector** 
- [ ] Activate **EMA Logger**
- [ ] Activate **Sentiment Analysis** (schedule 15:00 UTC)
- [ ] Activate **Sentiment Strategy Executor** (schedule 18:00 UTC)
- [ ] (Optional) Activate **EMA Crossover Bot** for live trading
