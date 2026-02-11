import json

with open('strategy_v1/workflows/sentiment-analysis-finbert-only.json', 'r') as f:
    data = json.load(f)

# Fix Calculate_Average_Sentiment to capture symbol
for node in data['nodes']:
    if node.get('name') == 'Calculate_Average_Sentiment':
        node['parameters']['jsCode'] = """const finbertResults = $json.results || [];
const symbol = $('loop_over_tickers').item.json.symbol;

if (finbertResults.length === 0) {
  return { json: { sentiment_score: 0, rationale: 'No articles analyzed', articleCount: 0, symbol: symbol } };
}

// Calculate average sentiment
const avgSentiment = finbertResults.reduce((sum, r) => sum + (r.sentiment || 0), 0) / finbertResults.length;

const rationale = `FinBERT avg sentiment: ${avgSentiment.toFixed(4)} across ${finbertResults.length} articles`;

return { json: { sentiment_score: avgSentiment, rationale: rationale, articleCount: finbertResults.length, symbol: symbol } };"""
        break

# Fix save_sentiment_to_db query - use $json.symbol
for node in data['nodes']:
    if node.get('name') == 'save_sentiment_to_db':
        # Use simple query without complex replacements
        node['parameters']['query'] = "INSERT INTO sentiment_scores (date, symbol, sentiment_score, rationale, article_count) VALUES ( CURRENT_DATE, '{{ $json.symbol }}', ROUND({{ Number($json.sentiment_score) }}::numeric, 4), '{{ $json.rationale }}', {{ Number($json.articleCount) }} ) ON CONFLICT (date, symbol) DO UPDATE SET sentiment_score = EXCLUDED.sentiment_score, rationale = EXCLUDED.rationale, article_count = EXCLUDED.article_count"
        break

with open('strategy_v1/workflows/sentiment-analysis-finbert-only.json', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Workflow fixed - symbol added to Calculate_Average_Sentiment, query simplified")
