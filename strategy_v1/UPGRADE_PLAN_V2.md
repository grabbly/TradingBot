# Upgrade Plan: v1.0 → v2.0

**Status:** Planning  
**Target Date:** February 2026  
**Current Issues:** Критический анализ показал фундаментальные проблемы v1.0

---

## Executive Summary

v1.0 - это proof-of-concept с серьёзными проблемами:
- ❌ Слишком простой sentiment analysis (GPT-4 на 10 статьях)
- ❌ Отсутствие технического анализа и фильтров
- ❌ Нет backtesting на исторических данных
- ❌ Примитивный risk management ($250/position = 1% exposure)
- ❌ Высокая корреляция активов (все tech)
- ❌ Ежедневный rebalancing генерирует шум и slippage

**v2.0 Goal:** Hybrid стратегия (sentiment + техничка + риск-менеджмент) с доказанной эффективностью.

---

## Phase 1: Validation & Foundation (Week 1-2)

**Цель:** Понять, работает ли v1.0 вообще

### 1.1 Backtest v1.0 Strategy (Priority: CRITICAL)
- [ ] **Task:** Симуляция v1.0 на исторических данных 2023-2025
  - Период: 2 года минимум
  - Данные: EODHD historical + sentiment proxy (random/simple)
  - Метрики: Total return, Sharpe ratio, max drawdown, win rate
- [ ] **Script:** Расширить `scripts/backtest_ema_strategy.py` для sentiment
- [ ] **Acceptance:** Если Sharpe < 0.5 или drawdown > 20% → stop, pivot
- [ ] **Effort:** 2 дня (Python, Alpaca historical API)

### 1.2 Analyze v1.0 Live Performance (если уже запущена)
- [ ] **Task:** Собрать метрики за первую неделю
  - Query `positions` table: win/loss ratio, avg P&L
  - Query `sentiment_scores`: стабильность топ-4
  - Check correlation: sentiment score vs. actual returns
- [ ] **Tools:** SQL queries + простой dashboard (matplotlib)
- [ ] **Acceptance:** Если корреляция < 0.3 → sentiment не работает
- [ ] **Effort:** 1 день

### 1.3 Cost Analysis
- [ ] **Task:** Посчитать реальные затраты v1.0
  - GPT-4 API: 7 symbols × 10 articles × 30 days = ~$X
  - Slippage: market orders на $250 × 2 trades/day
  - Opportunity cost: $100k capital earning 0% vs. SPY
- [ ] **Acceptance:** Если cost > expected returns → оптимизация нужна
- [ ] **Effort:** 0.5 дня

---

## Phase 2: Sentiment Upgrade (Week 3-4)

**Цель:** Заменить наивный GPT-4 анализ на production-ready систему

### 2.1 Replace GPT-4 with FinBERT
- [ ] **Task:** Интегрировать специализированную модель
  - Model: `ProsusAI/finbert` или `yiyanghkust/finbert-tone`
  - Deploy: Локально или HuggingFace Inference API (дешевле GPT)
  - Test: Сравнить accuracy на sample dataset (100 статей)
- [ ] **New workflow:** `sentiment-analysis-v2.json`
- [ ] **Acceptance:** Cost < 50% от GPT-4, accuracy >= GPT-4
- [ ] **Effort:** 3 дня (HuggingFace integration, testing)

### 2.2 Expand Data Sources
- [ ] **Task:** Добавить источники кроме новостей
  - **Reddit:** r/wallstreetbets, r/stocks mentions (Reddit API)
  - **X/Twitter:** Финансовые influencers (X API v2)
  - **StockTwits:** Community sentiment
- [ ] **Implementation:** 
  - n8n HTTP nodes для каждого API
  - Агрегация: weighted average (news: 40%, social: 60%)
- [ ] **Acceptance:** 50+ data points на symbol в день
- [ ] **Effort:** 4 дня (API setup, aggregation logic)

### 2.3 Sentiment Smoothing & Trend
- [ ] **Task:** Добавить 3-day moving average sentiment
  - Store daily sentiment в БД
  - Calculate MA3 в executor workflow
  - Use MA3 вместо raw score для топ-4
- [ ] **Acceptance:** Меньше whipsaws (< 2 changes/week в топ-4)
- [ ] **Effort:** 1 день (SQL query, Code node)

### 2.4 Enhanced Error Handling
- [ ] **Task:** Robust fallback для API failures
  - Retry с exponential backoff
  - Fallback на previous day sentiment (не 0.0)
  - Alert в Telegram при fallback
- [ ] **Effort:** 1 день

---

## Phase 3: Technical Analysis Integration (Week 5-6)

**Цель:** Добавить техничку для фильтрации и timing

### 3.1 EMA Filter (200-day Bull Bias)
- [ ] **Task:** Торговать только акции выше 200 EMA
  - Fetch daily bars от Alpaca (для 200 EMA нужно ~300 дней)
  - Calculate EMA200 в executor перед топ-4 selection
  - Filter: `sentiment_top_4.filter(price > ema200)`
- [ ] **Acceptance:** Backtest показывает улучшение Sharpe на 20%+
- [ ] **Effort:** 2 дня (historical data, EMA calc)

### 3.2 Entry Timing with EMA Crossovers
- [ ] **Task:** Использовать EMA 9/21 для timing
  - Calculate EMA9, EMA21 на дневных данных
  - Buy только при bullish cross (EMA9 > EMA21)
  - Sell при bearish cross или когда out of top-4
- [ ] **Acceptance:** Меньше false entries, выше win rate
- [ ] **Effort:** 2 дня (integ с существующим EMA code)

### 3.3 Volume & Momentum Filters
- [ ] **Task:** Добавить RSI и Volume
  - **RSI:** Покупка только если RSI < 70 (не overbought)
  - **Volume:** Volume > 20-day MA (confirmation)
- [ ] **Libraries:** `ta-lib` в Python (или pure JS calc)
- [ ] **Acceptance:** Backtest: снижение drawdown на 15%
- [ ] **Effort:** 2 дня

### 3.4 Macro Event Filter
- [ ] **Task:** Пропускать трейды перед FOMC/earnings
  - Fetch earnings calendar (Alpaca или FMP API)
  - Skip rebalance за 1 день до/после earnings
  - Manual FOMC dates в config
- [ ] **Acceptance:** Избегать volatility spikes
- [ ] **Effort:** 1 день

---

## Phase 4: Risk Management Overhaul (Week 7)

**Цель:** Перейти от toy-exposure к real trading

### 4.1 Percentage-Based Position Sizing (CRITICAL FIX)
- [ ] **Task:** Перейти на процентный риск вместо фиксированных сумм
  - **Risk per trade:** 1% от account balance (адаптируется автоматически)
  - **With $1,000:** max $10 risk per trade
  - **With $10,000:** max $100 risk per trade
  - **Formula:** Position size = Risk ($) / (Entry - Stop Loss)
- [ ] **Implementation:**
  - Calculate SL distance first (e.g., 2% below entry)
  - Position size = min(Account × 1% / SL_distance, Account × 25%)
  - Use fractional shares (Alpaca supports this)
- [ ] **Example:** 
  - Account: $1,000, Risk: $10 (1%)
  - Stock: $100, SL: $95 → Risk $5/share
  - Position: $10 / $5 = 2 shares ($200 position)
- [ ] **Gradual:** Start 0.5% risk, increase to 1% after 1 month
- [ ] **Acceptance:** No single trade loses > 1.5% account
- [ ] **Effort:** 1 day (dynamic calculation in Code node)

### 4.2 Stop-Loss & Take-Profit (MANDATORY)
- [ ] **Task:** Автоматические SL/TP для каждого трейда
  - **SL:** 2-3% от entry (depends on volatility, tighter for high vol)
  - **TP:** 2:1 reward-to-risk minimum (if SL 2%, TP 4%)
  - **Implementation:** Alpaca bracket orders (order type: "bracket")
  - **Trailing:** Optional trailing SL после +2% profit
- [ ] **For $1,000 account:**
  - SL $95 on $100 entry = $5 risk/share
  - Max position: 2 shares ($10 total risk)
  - TP $104 → $8 profit target (if hit)
- [ ] **Acceptance:** Every trade has SL/TP, no exceptions
- [ ] **Effort:** 2 дня (bracket orders API integration)

### 4.3 Portfolio Drawdown Limit
- [ ] **Task:** Pause trading при большом drawdown
  - Calculate max drawdown daily
  - If drawdown > 10% → pause на 1 неделю
  - Manual review & resume
- [ ] **Implementation:** Check в executor workflow
- [ ] **Effort:** 1 день

### 4.4 Sector Diversification
- [ ] **Task:** Расширить universe с 7 до 20-30 symbols
  - Добавить sectors: Energy (XOM), Healthcare (JNJ), Finance (JPM)
  - Topочка по сентименту, но limit 1-2 per sector
- [ ] **Acceptance:** Корреляция портфеля < 0.6
- [ ] **Effort:** 2 дня (новые symbols в БД, sector mapping)

---

## Phase 5: Operational Excellence (Week 8)

**Цель:** Production-ready мониторинг и автоматизация

### 5.1 Real-Time Dashboard
- [ ] **Task:** Визуализация метрик
  - **Tool:** Extend Treddy web app или Grafana
  - **Metrics:** Daily P&L, Sharpe ratio, positions heatmap
  - **Charts:** Sentiment trend, portfolio composition
- [ ] **Acceptance:** Dashboard обновляется real-time
- [ ] **Effort:** 3 дня (Flask/Chart.js)

### 5.2 Advanced Alerting
- [ ] **Task:** Telegram alerts для anomalies
  - Sentiment score < -0.5 (extreme bearish)
  - Position loss > 3% (approaching SL)
  - API failures (sentiment analysis down)
- [ ] **Effort:** 1 день (Telegram conditions)

### 5.3 A/B Testing Framework
- [ ] **Task:** Run v1.0 vs v2.0 parallel
  - Paper trading: v1.0 на $50k, v2.0 на $50k
  - Compare после 1 месяца
  - Switch to winner
- [ ] **Acceptance:** Statistical significance (t-test)
- [ ] **Effort:** 2 дня (duplicate workflows)

### 5.4 Automated Backtesting Pipeline
- [ ] **Task:** Weekly backtest на latest data
  - Cron job: каждое воскресенье
  - Re-run strategy на last 3 months
  - Email report если performance degrades
- [ ] **Effort:** 2 дня (Python script + cron)

---

## Phase 6: ML & Optimization (Optional - Month 3+)

**Цель:** Если v2.0 работает, добавить ML

### 6.1 Custom Sentiment Model
- [ ] **Task:** Train на собственных данных
  - Collect: 6 months sentiment + returns
  - Train: PyTorch classifier (sentiment → returns)
  - Deploy: Python server или HF space
- [ ] **Acceptance:** Accuracy > FinBERT на our universe
- [ ] **Effort:** 2 weeks (data prep, training, deploy)

### 6.2 Reinforcement Learning Portfolio
- [ ] **Task:** RL agent для position sizing
  - Use: Stable-Baselines3 (PPO)
  - State: sentiment, technical indicators, portfolio
  - Reward: Sharpe ratio
- [ ] **Acceptance:** Outperforms fixed allocation
- [ ] **Effort:** 3 weeks (RL is complex)

---

## Success Metrics (v2.0 vs v1.0)

| Metric | v1.0 Target | v2.0 Target | Measurement |
|--------|-------------|-------------|-------------|
| **Sharpe Ratio** | ? (unknown) | > 1.0 | Backtest + Live |
| **Annual Return** | ? | > 15% | Live (after fees) |
| **Max Drawdown** | ? | < 15% | Backtest + Live |
| **Win Rate** | ? | > 60% | Live trades |
| **Cost per Month** | ~$50 (GPT) | < $30 | API bills |
| **Correlation** | ~0.85 (tech) | < 0.6 | Portfolio |
| **Rebalance Freq** | Daily | 2-3x/week | Less churn |

---

## Timeline Summary

| Phase | Duration | Critical Path | Dependencies |
|-------|----------|---------------|--------------|
| 1. Validation | 2 weeks | Backtest v1.0 | None |
| 2. Sentiment | 2 weeks | FinBERT + sources | Phase 1 data |
| 3. Technical | 2 weeks | EMA filters | Historical bars |
| 4. Risk | 1 week | Position sizing | Backtest proof |
| 5. Operations | 1 week | Dashboard | Phase 2-4 done |
| 6. ML (opt) | 4+ weeks | Custom model | 6mo live data |

**Total:** 8 weeks для core v2.0, +4 weeks для ML.

---

## Decision Points

### After Phase 1 (Backtest):
- **If Sharpe < 0.5:** ❌ Stop v1.0, pivot to pure technical strategy
- **If Sharpe 0.5-1.0:** ⚠️ Proceed with caution, focus on Phase 2-3
- **If Sharpe > 1.0:** ✅ v1.0 works, optimize in v2.0

### After Phase 4 (v2.0 Paper):
- **If v2.0 < v1.0:** ❌ Rollback, iterate
- **If v2.0 >> v1.0:** ✅ Go live with real capital

### After 3 Months Live:
- **If losing money:** ❌ Pause, deep review
- **If flat/small gains:** ⚠️ Continue with tweaks
- **If profitable:** ✅ Scale up, add ML

---

## Risk Mitigation

1. **Never skip backtesting** - код без proof = gambling
2. **Start small** - $1k real → $5k → $20k (gradual)
3. **Manual override** - всегда можно остановить
4. **Diversify strategies** - не всё в sentiment (run EMA bot parallel)
5. **Paper trading first** - каждый Phase 1 месяц на paper

---

## Resources Needed

- **APIs:** 
  - FinBERT (free via HuggingFace Inference API)
  - Reddit Basic ($0, rate limited) or Premium ($50/mo)
  - X Developer Basic Tier ($0-100/mo depending on needs)
  - Alpaca Paper (free), Real ($0 commission)
- **Compute:** Treddy server sufficient, ML может требовать GPU (cloud)
- **Time:** ~20 часов/неделю на development
- **Capital Strategy:**
  - **Phase 1-2 (Weeks 1-4):** Paper trading only
  - **Phase 3-4 (Weeks 5-7):** $500 real (50% of capital, test mode)
  - **Phase 5+ (Week 8+):** $1,000 full (после proof of concept)
  - **Growth:** Reinvest 50% profits, withdraw 50% (risk management)
  - **Scale:** После 6 months profitable → increase to $2-5k

---

## Next Steps (Immediate)

1. ✅ Finish organizing v1.0 files (done)
2. ⏩ **Run Phase 1.1 backtest** (start tomorrow)
3. ⏩ Create `strategy_v2/` folder для новых файлов
4. ⏩ Document v1.0 live results (if running)

---

**Last Updated:** 2026-01-07  
**Owner:** Gabby  
**Review:** Weekly on Sundays  
**Starting Capital:** $1,000 (real), paper first for Phase 1-2

---

## Appendix: Small Account Adaptation ($1,000 Start)

### Realistic Expectations

**Monthly Returns:**
- **Conservative:** 3-5% ($30-50/month) — это уже хорошо
- **Aggressive:** 8-12% ($80-120/month) — возможно, но с drawdowns
- **Exceptional:** 15%+ — редко sustainable, не планируй на это

**Time to Double:**
- At 5%/month: ~15 months to $2,000 (compounded)
- At 10%/month: ~7 months to $2,000
- Reality: Expect 6-12 months с учётом drawdowns

**Challenges с Small Account:**
- ❌ Commissions hurt less с Alpaca (no fees), но spread всё равно ест
- ❌ Psychological pressure: каждые $10 = 1% аккаунта
- ❌ Limited diversification: можешь держать 2-4 позиции max
- ✅ Fractional shares solve position sizing (Alpaca supports)
- ✅ Lower stress vs. large capital (можешь позволить учиться)

### Position Sizing Examples

**Account $1,000:**
- Risk per trade: $10 (1%)
- Max position size: $250 (25% account, если tight SL)
- Typical: 2-4 active positions × $150-250 each
- Example trade:
  - Buy AAPL @ $180, SL @ $176 (2.2% or $4/share risk)
  - Position: $10 risk / $4 = 2.5 shares ($450 total)
  - TP @ $188 (4.4% or $8/share) → $20 profit if hit

**Account $2,500 (после роста):**
- Risk per trade: $25 (1%)
- Max positions: 3-5 × $400-600 each
- Same %риска, но больше flexibility

**Account $10,000:**
- Risk per trade: $100 (1%)
- Can hold 4-6 positions comfortably
- Now matches expanded plan ($1000-1500/position)

### Broker Requirements

**Must Have:**
- ✅ Fractional shares (Alpaca, Schwab, Fidelity, Robinhood)
- ✅ No commissions (Alpaca perfect)
- ✅ API access for automation (Alpaca Paper + Real)
- ✅ Bracket orders for SL/TP (Alpaca supports)

**Optional but Nice:**
- Extended hours trading
- Options (for hedging later, ignore сейчас)
- Margin (NOT recommended для $1k — too risky)

### Prop Firm Alternative (Advanced)

Если хочешь больше exposure без риска своих денег:
- **Funded accounts:** Пройди challenge ($100-300 fee), get $10k-50k funded
- **Popular:** Apex Trader, Topstep, FundedNext
- **Profit split:** 80-90% yours, firm gets 10-20%
- **Risk:** Only lose challenge fee, не свой капитал
- **Recommendation:** Сначала proof v2.0 на своём $1k, потом try prop challenge

### Risk Management Checklist

- [ ] Never risk >1% per trade ($10 on $1k)
- [ ] Max 3-4 open positions simultaneously
- [ ] Stop trading if daily loss >3% ($30)
- [ ] Stop trading if weekly loss >5% ($50)
- [ ] Pause 1 week if monthly loss >10% ($100)
- [ ] Never add to losing position (no averaging down)
- [ ] Never remove SL once set (discipline > hope)
- [ ] Journal every trade (why entered, result, lessons)
