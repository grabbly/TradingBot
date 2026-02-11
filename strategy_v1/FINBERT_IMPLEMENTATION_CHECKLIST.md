# Phase 2.1.3 Implementation Checklist: FinBERT in n8n

**Status:** Ready for implementation  
**Date:** 2026-02-01  
**Owner:** TradingBot Team  
**Objective:** Replace GPT-4 with FinBERT, save $50/month

---

## Pre-Flight Checklist

- [ ] **HuggingFace Account Ready**
  - Go to https://huggingface.co/join
  - Create account (or use existing)
  - Verify email

- [ ] **API Token Generated**
  - Go to https://huggingface.co/settings/tokens
  - Click "New token"
  - Name: `n8n-finbert-trading`
  - Role: `Read`
  - Copy token (looks like: `hf_xxxxxxxxxxxxxxxxxxx`)
  - **SAVE SECURELY** (not in git!)

- [ ] **Backup Current Workflow**
  ```bash
  cd /Users/gabby/git/TradingBot/strategy_v1/workflows
  cp sentiment-analysis.json sentiment-analysis_gpt4_backup_20260201.json
  git add sentiment-analysis_gpt4_backup_20260201.json
  git commit -m "Backup: GPT-4 version before FinBERT migration"
  ```

---

## n8n UI Implementation (Manual)

### Phase 1: Preparation (5 min)

**Step 1.1:** Open n8n Workflow
- Navigate to: Workflows → "sentiment-analysis"
- Click "Edit" (pencil icon)
- Take screenshot for reference

**Step 1.2:** Identify Nodes to Replace
- Find node: `AI Agent1` (LangChain AI Agent)
- Find node: `OpenAI Chat Model`
- These two nodes form the GPT-4 sentiment analysis pipeline
- Keep all other nodes as-is

**Step 1.3:** Export Backup
- Click menu (three dots) → "Export Workflow"
- Save as: `sentiment-analysis_gpt4_full_backup.json`
- Upload to repo as: `strategy_v1/workflows_v1.0_backup/sentiment-analysis_gpt4_full.json`

---

### Phase 2: Delete Old Nodes (5 min)

**Step 2.1:** Delete `AI Agent1`
- Right-click on node → "Delete"
- Confirm deletion

**Step 2.2:** Delete `OpenAI Chat Model`
- Right-click on node → "Delete"
- Confirm deletion

**Step 2.3:** Save Checkpoint
- Click "Save" (Cmd+S or button)
- Workflow should still be executable (other paths exist)

---

### Phase 3: Add FinBERT HTTP Node (10 min)

**Step 3.1:** Add HTTP Request Node
- Click "Add Node" (+ button in canvas)
- Search: "HTTP Request"
- Click to add

**Step 3.2:** Configure Node Name
- In node settings, set: `Name: "FinBERT_Analyze_Sentiment"`
- Color: Yellow (optional, for visibility)

**Step 3.3:** Configure HTTP Request Details
In the node's "Parameters" tab:

| Field | Value |
|-------|-------|
| **Method** | `POST` |
| **URL** | `https://api-inference.huggingface.co/models/ProsusAI/finbert` |
| **Authentication** | `Header Auth` |

**Step 3.4:** Add Authentication Header
- In "Authentication" section, click "+ Add Header"
- Header Name: `Authorization`
- Header Value: `Bearer {{$env.HF_API_TOKEN}}`
  - (Replace `$env.HF_API_TOKEN` with your actual token or use n8n Variable)

**Step 3.5:** Configure Request Body
- Body type: `JSON`
- Body content:
  ```json
  {
    "inputs": "{{$json.title}} {{$json.content}}"
  }
  ```
  - Adjust field names to match your data source (`title`, `content`, etc.)

**Step 3.6:** Save Node
- Click "Save" (Cmd+S)

---

### Phase 4: Add Output Parser (5 min)

**Step 4.1:** Add Code Node
- Click "Add Node" → Search: "Code"
- Click to add

**Step 4.2:** Configure Code Node
- Name: `Parse_FinBERT_Output`
- Language: `JavaScript`
- Paste code:

```javascript
// Parse FinBERT response: [{ label: "positive|negative|neutral", score: 0.95 }]
const result = $json[0];

// Convert label + score to -1 to +1 sentiment scale
let sentiment = 0.0;
if (result.label === 'positive') {
  sentiment = result.score;
} else if (result.label === 'negative') {
  sentiment = -result.score;
} else {
  sentiment = 0.0;  // neutral
}

// Round to 4 decimal places
sentiment = Math.round(sentiment * 10000) / 10000;

return {
  json: {
    sentiment: sentiment,
    label: result.label,
    confidence: result.score,
    rationale: `FinBERT: ${result.label} (${(result.score * 100).toFixed(1)}%)`
  }
};
```

**Step 4.3:** Save Code Node
- Click "Save" (Cmd+S)

---

### Phase 5: Connect Nodes (10 min)

**Step 5.1:** Identify Connection Points
- Find node that outputs articles: likely `Get_Unanalyzed_News` (PostgreSQL query)
- This should connect TO `FinBERT_Analyze_Sentiment`

**Step 5.2:** Draw Connection
- Click small circle/dot on right edge of `Get_Unanalyzed_News`
- Drag line to left edge of `FinBERT_Analyze_Sentiment`
- Release to connect

**Step 5.3:** Connect Output Parser
- Click right edge of `FinBERT_Analyze_Sentiment`
- Drag line to `Parse_FinBERT_Output`
- Connect

**Step 5.4:** Connect to Next Node
- From `Parse_FinBERT_Output`, connect to next step
- Likely: `format_output_as_json` or similar
- Draw connection

**Step 5.5:** Verify Flow
- Visual: `Get_Unanalyzed_News` → `FinBERT_Analyze_Sentiment` → `Parse_FinBERT_Output` → rest of workflow
- No dangling nodes

---

### Phase 6: Add n8n Environment Variable (5 min)

**Step 6.1:** Access n8n Settings
- Click user menu (bottom left) → "Settings"
- Go to "Variables" tab

**Step 6.2:** Create New Variable
- Click "+ Add Variable"
- Name: `HF_API_TOKEN`
- Scope: `All workflows`
- Value: `hf_xxxxxxxxxxxxxxxxxxxxx` (your HuggingFace token)
- Click "Save"

**Step 6.3:** Update Node Reference (if needed)
- In `FinBERT_Analyze_Sentiment` node, update header value:
  - Old: `Bearer {{$env.HF_API_TOKEN}}`
  - New: `Bearer {{$env.HF_API_TOKEN}}` (should already work)

---

### Phase 7: Test on Sample Data (10 min)

**Step 7.1:** Execute Workflow
- Click "Test workflow" or "Execute workflow"
- Select test input (if needed) or use live data

**Step 7.2:** Verify Output
- Check execution logs
- FinBERT_Analyze_Sentiment node should return: `[{ label: "...", score: ... }]`
- Parse_FinBERT_Output should return: `{ sentiment: -1 to +1, label: ..., confidence: ... }`

**Step 7.3:** Manual Spot Check
- Find 5-10 sample articles
- Verify FinBERT labels make sense:
  - Positive article → sentiment ≈ +0.5 to +1.0
  - Negative article → sentiment ≈ -1.0 to -0.5
  - Neutral article → sentiment ≈ -0.2 to +0.2

**Step 7.4:** Document Results
- Screenshot successful execution
- Add to: `strategy_v1/FINBERT_IMPLEMENTATION_LOG.md`

---

### Phase 8: Deploy & Monitor (5 min)

**Step 8.1:** Activate Workflow
- Set workflow to "Active" (toggle switch, top right)
- Confirm status: "Active"

**Step 8.2:** Monitor First 24 Hours
- Check n8n dashboard for errors
- Watch PostgreSQL `sentiment_scores` table for updates
- Verify daily sentiment reports in Telegram (if enabled)

**Step 8.3:** Compare Metrics
- After 24h, run:
  ```sql
  SELECT symbol, AVG(sentiment) as avg_sentiment, COUNT(*) as count
  FROM sentiment_scores
  WHERE DATE(date) = CURRENT_DATE
  GROUP BY symbol
  ORDER BY avg_sentiment DESC;
  ```
- Expected: Distribution similar to baseline (no wild outliers)

**Step 8.4:** Log Completion
- Update `strategy_v1/TASKS.md` → Task 2.1.3 as COMPLETE
- Tag commit: `git tag -a v2.1.3-finbert-deployed -m "FinBERT deployed in n8n"`
- Push: `git push origin main --tags`

---

## Troubleshooting

### Error: "Cannot find module 'httpRequest'"
- Solution: Ensure you're using n8n "HTTP Request" node (built-in), not a custom node

### Error: "401 Unauthorized" from HuggingFace
- Solution: 
  1. Check token is correct: https://huggingface.co/settings/tokens
  2. Verify token hasn't expired
  3. Try manual curl test:
     ```bash
     curl -X POST https://api-inference.huggingface.co/models/ProsusAI/finbert \
       -H "Authorization: Bearer <YOUR_TOKEN>" \
       -H "Content-Type: application/json" \
       -d '{"inputs":"Tesla stock rises today"}'
     ```

### Error: "Rate limit exceeded (30k/month)"
- Solution: 
  1. Upgrade HuggingFace to paid tier ($9/month)
  2. OR reduce batch size (analyze fewer articles per day)
  3. OR wait until next month's quota resets

### Sentiment values seem off (all near 0)
- Solution: 
  1. Check article text is being passed correctly (log raw input)
  2. Verify output parser code is correct
  3. Compare with manual FinBERT test

---

## Success Metrics

After 48 hours, verify:

- [ ] **No errors in logs** (check n8n dashboard)
- [ ] **Sentiment scores saved to DB** (~100-200 per day)
- [ ] **Avg response time <1s** per article
- [ ] **HuggingFace usage <5% of monthly quota**
- [ ] **Telegram alerts sent** (if configured)
- [ ] **Portfolio rebalancing triggered** on sentiment signals

---

## Rollback Plan

If issues occur:

```bash
# 1. Stop workflow in n8n UI
# 2. Restore backup
cd /Users/gabby/git/TradingBot/strategy_v1/workflows
cp sentiment-analysis_gpt4_backup_20260201.json sentiment-analysis.json

# 3. Re-import in n8n:
# → n8n UI → Workflows → Import → sentiment-analysis.json

# 4. Activate workflow
# → n8n UI → sentiment-analysis → toggle Active

# 5. Commit rollback
git add sentiment-analysis.json
git commit -m "Rollback: Reverted FinBERT, restored GPT-4 (temporary)"
```

---

## Documentation Updates

After successful deployment:

1. Update [strategy_v1/STRATEGY.md](../STRATEGY.md)
   - Change: "AI Agent (GPT-4)" → "FinBERT via HTTP"
   - Add cost: ~$10/month vs $59/month

2. Update [strategy_v1/TASKS.md](../TASKS.md)
   - Mark Task 2.1.3 as COMPLETE
   - Update Task 2.1.4 (cost comparison)

3. Create report: `reports/finbert_deployment_20260201.md`
   - Performance metrics
   - Cost savings
   - Accuracy comparison

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Pre-Flight | 5 min | Ready |
| Delete Old Nodes | 5 min | Ready |
| Add FinBERT HTTP | 10 min | Ready |
| Add Parser | 5 min | Ready |
| Connect Nodes | 10 min | Ready |
| Config Env Var | 5 min | Ready |
| Test | 10 min | Ready |
| Deploy | 5 min | Ready |
| **Total** | **55 min** | ✅ |

---

## Next Steps (After Deployment)

1. **Week 2:** Compare FinBERT vs baseline sentiment on 1-week data
2. **Week 3:** Run parallel backtest with FinBERT sentiment
3. **Week 4:** Full validation & decision on permanent switch
4. **Week 5:** Deprecate GPT-4 credentials from n8n

