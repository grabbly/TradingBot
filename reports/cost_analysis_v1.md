# Cost Analysis: v1.0 Sentiment Strategy
**Date:** 2026-01-08  
**Analysis Period:** Monthly costs for $10,000 portfolio

---

## 1. Current GPT-4 Sentiment Analysis Costs

### API Usage
- **Symbols:** 7 (AAPL, AMZN, GOOGL, META, MSFT, NVDA, TSLA)
- **Articles per symbol per day:** ~10
- **Trading days per month:** ~20
- **Total API calls per month:** 7 × 10 × 20 = **1,400 calls/month**

### GPT-4 Pricing (as of Jan 2026)
- **Input tokens:** ~$0.03 per 1,000 tokens
- **Output tokens:** ~$0.06 per 1,000 tokens

### Token Estimation per Call
- **Input:** ~1,000 tokens (article text + prompt)
- **Output:** ~200 tokens (sentiment analysis response)

### Monthly Cost Calculation
```
Input cost:  1,400 calls × 1,000 tokens × $0.03/1k = $42.00
Output cost: 1,400 calls × 200 tokens × $0.06/1k  = $16.80
Total GPT-4 cost: $58.80/month
```

**Annual:** $705.60

---

## 2. Alternative: FinBERT (Open-Source)

### Cost Breakdown
- **Model:** ProsusAI/finbert (Free, open-source)
- **Hosting:** 
  - Option A: Local (Mac/Server) - $0/month
  - Option B: HuggingFace Inference API - ~$0-10/month
- **News API:** EODHD ($9.99/month) or alternatives

### Monthly Cost
```
FinBERT inference: $0 (local) to $10 (hosted)
News API: $10
Total: $10-20/month
```

**Annual:** $120-240

### Savings
```
GPT-4:    $58.80/month
FinBERT:  $15/month (avg)
Savings:  $43.80/month = $525.60/year
Cost reduction: 74%
```

---

## 3. Trading Costs

### Commission (Alpaca)
- **Buy/Sell commission:** $0 (commission-free) ✅

### Slippage
Based on backtest: 588 rebalances in 751 days = 0.78 rebalances/day

**Assumptions:**
- Average position size: $2,500 (25% of $10k)
- Slippage: 0.1% per trade
- Trades per rebalance: ~2 (1 sell + 1 buy)

**Monthly Calculation:**
```
Rebalances per month: 0.78/day × 20 days = 15.6
Trades per month: 15.6 × 2 = 31.2
Volume per month: 31.2 × $2,500 = $78,000

Slippage cost: $78,000 × 0.1% = $78/month
```

**Annual:** $936

### Market Impact (Large Orders)
- Current portfolio: $10,000 → minimal impact
- At $100k scale: Impact increases to ~0.15%
- At $1M scale: Need to split orders

---

## 4. Total Operating Costs

### Monthly Breakdown

| Cost Category | GPT-4 Approach | FinBERT Approach |
|---------------|----------------|------------------|
| Sentiment Analysis | $58.80 | $15.00 |
| Trading (Slippage) | $78.00 | $78.00 |
| Commission | $0.00 | $0.00 |
| **Total** | **$136.80** | **$93.00** |

### Annual Total
- **GPT-4:** $1,641.60/year
- **FinBERT:** $1,116/year
- **Savings:** $525.60/year (32% reduction)

---

## 5. Break-Even Analysis

### For $10,000 Portfolio

**Monthly Costs:**
- GPT-4: $136.80
- FinBERT: $93.00

**Required Returns to Break Even:**
```
GPT-4:   $136.80 / $10,000 = 1.37% per month = 16.4% annual
FinBERT: $93.00 / $10,000 = 0.93% per month = 11.2% annual
```

### Actual Strategy Performance (from backtest)
- **3-year return:** +127.78%
- **Annualized:** ~31.5% per year
- **Monthly avg:** ~2.3% per month

### Profit After Costs

**Monthly:**
```
Gross return:  2.3% × $10,000 = $230
GPT-4 costs:   -$136.80
Net profit:    $93.20 (0.93% net return)

FinBERT costs: -$93.00
Net profit:    $137.00 (1.37% net return)
```

**Annual:**
```
Gross return:  31.5% × $10,000 = $3,150
GPT-4 costs:   -$1,642
Net profit:    $1,508 (15.1% net return)

FinBERT costs: -$1,116
Net profit:    $2,034 (20.3% net return)
```

**✅ Strategy remains profitable with both approaches**

---

## 6. Opportunity Cost

### Benchmark: SPY Buy-and-Hold
- **Expected annual return:** ~10% (historical avg)
- **Monthly:** ~0.83%
- **Annual profit on $10k:** $1,000

### Strategy vs. SPY
```
Strategy (FinBERT):  $2,034 net profit
SPY baseline:        $1,000
Alpha:               +$1,034 (103% better)

Strategy (GPT-4):    $1,508 net profit
SPY baseline:        $1,000
Alpha:               +$508 (51% better)
```

**Conclusion:** Strategy beats SPY even with costs, FinBERT approach delivers 2x SPY returns.

---

## 7. Scalability Analysis

### At Different Portfolio Sizes

| Portfolio Size | Monthly Costs (FinBERT) | Break-Even Return | Net Return @ 2.3% |
|----------------|-------------------------|-------------------|-------------------|
| $10,000 | $93 | 0.93% | $137 (1.37%) |
| $50,000 | $143 | 0.29% | $1,007 (2.01%) |
| $100,000 | $243 | 0.24% | $2,057 (2.06%) |
| $500,000 | $743 | 0.15% | $10,757 (2.15%) |

**Notes:**
- Slippage increases slightly at larger sizes
- API costs remain relatively fixed
- Cost % decreases as portfolio grows
- Strategy becomes MORE profitable at scale

---

## 8. Recommendations

### ✅ Immediate Actions
1. **Switch to FinBERT** - Save $525/year (32% cost reduction)
2. **Fix EODHD API** or migrate to alternative news source
3. **Monitor slippage** - Track actual vs. assumed 0.1%

### 🚀 Phase 2 Optimizations
1. **Reduce rebalancing frequency** 
   - Currently: 74.5% of days (588/751)
   - Target: 50% of days with sentiment threshold
   - Potential savings: ~$30/month in slippage

2. **Batch news fetching**
   - Cache news for 24 hours
   - Reduce API calls by ~50%

3. **Portfolio size**
   - At $50k+: Cost % drops below 0.3%
   - Strategy economics improve significantly

### ⚠️ Risk Considerations
1. **High turnover** (74.5% rebalance rate) = high slippage
2. **Small account** ($10k) = costs eat 0.93% monthly
3. **News API dependency** - need reliable source

---

## 9. Summary

| Metric | Value |
|--------|-------|
| **Current Approach** | GPT-4 + Alpaca |
| **Monthly Cost** | $136.80 |
| **Break-Even Return** | 1.37%/month |
| **Actual Return** | 2.3%/month (gross) |
| **Net Return** | 0.93%/month |
| **Annual Net Return** | 15.1% |
| | |
| **Recommended Approach** | FinBERT + Alpaca |
| **Monthly Cost** | $93.00 |
| **Break-Even Return** | 0.93%/month |
| **Net Return** | 1.37%/month |
| **Annual Net Return** | 20.3% |
| **vs. SPY** | +103% better |

---

## 10. Conclusion

✅ **Strategy is economically viable** even at $10k scale

✅ **FinBERT migration** is critical for cost efficiency (32% savings)

✅ **Profitability improves** significantly at larger portfolio sizes

⚠️ **High turnover** (74.5%) is main cost driver - Phase 3 optimizations needed

🎯 **Next Step:** Implement Phase 2 (FinBERT) to unlock full profitability

---

**Prepared by:** TradingBot Analysis  
**Version:** v1.0  
**Date:** 2026-01-08
