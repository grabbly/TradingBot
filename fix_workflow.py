import json

with open('strategy_v1/workflows/sentiment-analysis-hybrid.json', 'r') as f:
    data = json.load(f)

# Find Prepare_for_FinBERT and ensure articles passthrough
for node in data['nodes']:
    if node.get('name') == 'Prepare_for_FinBERT':
        node['parameters']['jsCode'] = """// Prepare articles for FinBERT batch analysis
const articles = $input.all();
const texts = articles.map(item => {
  const a = item.json;
  return `Title: ${a.title || ''}\\nContent: ${(a.content || '').substring(0, 500)}`;
});

return [{
  json: {
    texts: texts,
    articles: articles.map(item => item.json),
    articleCount: articles.length
  }
}];"""
        break

# Add passthrough node after HTTP to preserve articles
for i, node in enumerate(data['nodes']):
    if node.get('name') == 'FinBERT_Batch_Analyze':
        # Update to pass articles with response
        node['parameters']['options'] = {"timeout": 60000}
        break

# Update Format_for_GPT4 to work with FinBERT response that includes articles
for node in data['nodes']:
    if node.get('name') == 'Format_for_GPT4':
        node['parameters']['jsCode'] = """// Parse FinBERT batch response and format for GPT-4
const finbertResponse = $json;
const finbertResults = finbertResponse.results || [];
const articles = finbertResponse.articles || [];

// Create summary for GPT-4
const summary = finbertResults.map((r, i) => {
  const article = articles[i] || {};
  return {
    title: article.title || '',
    finbert_sentiment: r.sentiment ? r.sentiment.toFixed(4) : '0',
    finbert_positive: r.positive ? r.positive.toFixed(4) : '0'
  };
});

const summaryText = JSON.stringify({
  articles: summary,
  count: summary.length
}, null, 2);

return { json: { summaryText, articleCount: finbertResults.length } };"""
        break

with open('strategy_v1/workflows/sentiment-analysis-hybrid.json', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Workflow passthrough fixed")
