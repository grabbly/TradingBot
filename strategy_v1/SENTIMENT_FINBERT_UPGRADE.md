# Task 2.1.3: Replace GPT-4 with FinBERT in n8n Workflow

**Date:** 2026-02-01  
**Task:** Update `sentiment-analysis.json` workflow to use FinBERT instead of GPT-4o  
**Expected Savings:** $50/month (~32% cost reduction)

---

## Current Setup (GPT-4o)
- **Node:** `AI Agent1` → `OpenAI Chat Model`
- **Cost:** ~$59/month for sentiment analysis
- **Latency:** 1-2s per article (API call overhead)
- **Accuracy:** High, but expensive for production

## New Setup (FinBERT via HuggingFace)
- **Node:** HTTP Request to HuggingFace Inference API
- **Cost:** ~$0-10/month (free tier + API)
- **Latency:** <500ms per article (optimized inference)
- **Accuracy:** Financial domain fine-tuned, proven for news sentiment

---

## Implementation Options

### Option A: HuggingFace Inference API (Recommended)
**Pros:**
- Free tier: 30k requests/month
- Easy HTTP integration in n8n
- Hosted & managed by HuggingFace

**Cons:**
- Rate limited on free tier
- Need API token

**Setup:**
1. Create HuggingFace account: https://huggingface.co
2. Generate API token: https://huggingface.co/settings/tokens
3. Replace GPT-4 node with HTTP Request to:
   ```
   POST https://api-inference.huggingface.co/models/ProsusAI/finbert
   Headers:
     Authorization: Bearer <HF_API_TOKEN>
   Body:
     {
       "inputs": "<ARTICLE_TITLE_AND_CONTENT>"
     }
   ```
4. Parse output (array of label scores) → convert to -1 to +1 scale

### Option B: Local FinBERT Server
**Pros:**
- No API calls, completely free
- Full control, no rate limits
- Can run on GPU server (192.168.1.3)

**Cons:**
- Need to set up separate inference server
- More infrastructure

**Setup:**
- Would require FastAPI + FinBERT model on server
- n8n calls `http://192.168.1.3:8000/analyze` for sentiment

---

## n8n Workflow Changes

### Current GPT-4 Node
```json
{
  "name": "AI Agent1",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "toolsAgentOptions": {
      "model": "gpt-4o"
    }
  }
}
```

### Proposed FinBERT HTTP Node
```json
{
  "name": "FinBERT_Analyze_Sentiment",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "https://api-inference.huggingface.co/models/ProsusAI/finbert",
    "method": "POST",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "httpHeaderAuth",
    "headers": {
      "Authorization": "Bearer {{$env.HF_API_TOKEN}}"
    },
    "bodyParametersUi": "json",
    "body": {
      "inputs": "={{$json.article_title}} {{$json.article_content}}"
    }
  }
}
```

### Output Parsing Node
```json
{
  "name": "Parse_FinBERT_Output",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "jsCode": "// FinBERT returns: [{ \"label\": \"positive\", \"score\": 0.95 }, ...]\nconst result = $json[0];\nconst sentiment = \n  result.label === 'positive' ? result.score :\n  result.label === 'negative' ? -result.score :\n  0.0;\n\nreturn {\n  sentiment: Math.round(sentiment * 10000) / 10000,\n  label: result.label,\n  confidence: result.score\n};"
  }
}
```

---

## Migration Checklist

- [ ] Create HuggingFace account & get API token
- [ ] Add `HF_API_TOKEN` to n8n environment variables
- [ ] Backup current workflow: `cp sentiment-analysis.json sentiment-analysis_gpt4_backup.json`
- [ ] Replace AI Agent + OpenAI nodes with HTTP Request to HuggingFace
- [ ] Add output parsing code node
- [ ] Test on 5-10 sample articles
- [ ] Verify sentiment scores align with expectations (range: -1 to +1)
- [ ] Run full 24-hour test cycle (collect all articles → analyze → log)
- [ ] Compare FinBERT vs GPT-4 accuracy on shared test set
- [ ] Commit & tag as `sentiment-analysis-v2.1`

---

## Cost Comparison

| Metric | GPT-4o | FinBERT |
|--------|--------|---------|
| Cost/month | $59 | $0-10 |
| Response time | 1-2s | <500ms |
| Requests/month | 1,400 | 1,400 |
| Model accuracy | High | High (financial domain) |
| **Savings** | — | **$49-59** |

---

## Rollback Plan
If FinBERT quality issues arise:
1. Revert workflow: `git checkout HEAD -- sentiment-analysis.json`
2. Restart workflow in n8n
3. Resume GPT-4 analysis (no data loss, just slower)

---

## Next Steps
1. **Immediate:** Set up HuggingFace account + API token
2. **Week 1:** Update workflow & test on sample data
3. **Week 2:** Run parallel comparison (FinBERT vs GPT-4) on real news
4. **Week 3:** Deploy FinBERT full-time, deprecate GPT-4
5. **Week 4:** Monitor performance & fine-tune if needed

**Timeline:** 2-3 weeks to full deployment

---

## FinBERT Model Details
- **Model:** ProsusAI/finbert
- **Fine-tuned on:** Financial news corpus (Reuters + Benzinga)
- **Classes:** positive, negative, neutral
- **Output:** Per-class probability scores
- **Recommended threshold:** confidence > 0.5 for reliable signals

---

## References
- HuggingFace FinBERT: https://huggingface.co/ProsusAI/finbert
- HuggingFace Inference API: https://huggingface.co/docs/api-inference
- n8n HTTP Request node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/

