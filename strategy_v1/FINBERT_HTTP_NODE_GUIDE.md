# FinBERT HTTP Node Configuration for n8n

This file provides the exact node configuration to replace the GPT-4 AI Agent node in `sentiment-analysis.json`.

## Step-by-Step Manual Update in n8n UI

### 1. Export Current Workflow
- Open n8n → Workflows → sentiment-analysis
- Click "Export" button (top right) → save backup locally

### 2. Delete Old GPT-4 Nodes
- Delete node: `AI Agent1` (the LangChain AI Agent)
- Delete node: `OpenAI Chat Model` (GPT-4 model config)
- Keep node: `format_output_as_json` (reuse for output formatting)

### 3. Add New HTTP Request Node
- Click "Add Node" → search "HTTP Request"
- Name it: `FinBERT_Analyze_Sentiment`
- Configure as follows:

```
Method: POST
URL: https://api-inference.huggingface.co/models/ProsusAI/finbert

Authentication: Header Auth
  Header name: Authorization
  Header value: Bearer {{env_hf_api_token}}

Body (JSON):
{
  "inputs": "{{$json.combined_text}}"
}
```

### 4. Add Output Parser Node (Code)
- Click "Add Node" → search "Code"
- Name it: `Parse_FinBERT_Result`
- Language: JavaScript
- Code:

```javascript
// Parse FinBERT response: [{ label: "positive", score: 0.95 }]
const result = $json[0];

// Convert to -1 to +1 scale
const sentiment = 
  result.label === 'positive' ? result.score :
  result.label === 'negative' ? -result.score :
  0.0;

return {
  json: {
    sentiment: Math.round(sentiment * 10000) / 10000,
    label: result.label,
    confidence: result.score,
    rationale: `FinBERT classified as ${result.label} (confidence: ${(result.score * 100).toFixed(1)}%)`
  }
};
```

### 5. Connect Nodes
```
Get_Unanalyzed_News 
  ↓
[Prepare article text]
  ↓
FinBERT_Analyze_Sentiment (HTTP)
  ↓
Parse_FinBERT_Result (Code)
  ↓
format_output_as_json (existing)
  ↓
save_sentiment_to_db (existing)
```

### 6. Add Environment Variable (n8n Settings)
- Go to Settings → Variables
- Add new variable:
  - Name: `env_hf_api_token`
  - Value: `hf_xxxxxxxxxxxxxxxxxxxxx` (from HuggingFace)
  - Scope: All workflows

### 7. Test
- Save workflow
- Create test execution with a sample article
- Verify output: sentiment should be between -1 and +1

---

## Alternative: Pre-Built JSON

If you want to programmatically update the workflow, here's a minimal node definition:

```json
{
  "id": "finbert-http-node",
  "name": "FinBERT_Analyze_Sentiment",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [640, 784],
  "parameters": {
    "url": "https://api-inference.huggingface.co/models/ProsusAI/finbert",
    "method": "POST",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "httpHeaderAuth",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Authorization",
          "value": "Bearer {{env_hf_api_token}}"
        }
      ]
    },
    "bodyParametersUi": "json",
    "body": {
      "inputs": "={{$json.article_title}} {{$json.article_content}}"
    },
    "options": {
      "timeout": 10,
      "redirect": {
        "followRedirects": true
      }
    }
  },
  "credentials": {
    "httpHeaderAuth": {
      "id": "hf_auth_credential",
      "name": "HuggingFace API"
    }
  }
}
```

---

## Troubleshooting

### "401 Unauthorized"
- Check HF_API_TOKEN is set correctly in n8n environment
- Verify token is not expired at https://huggingface.co/settings/tokens

### "Rate limit exceeded"
- You're on HuggingFace free tier (30k/month)
- Upgrade to paid tier ($9/month for unlimited)
- OR reduce article batch size

### "No label found"
- Model output format changed
- Add debug step to log raw response: `console.log($json)`

---

## Monitoring & Metrics

After deployment, track:
1. **Latency:** Average API response time (target: <500ms)
2. **Accuracy:** Compare FinBERT labels vs manual review on sample
3. **Cost:** Monitor HuggingFace usage dashboard
4. **Coverage:** % of articles with valid sentiment (target: >95%)

---

## Rollback
If issues arise:
```bash
git checkout HEAD -- strategy_v1/workflows/sentiment-analysis.json
# Then re-import workflow in n8n
```

