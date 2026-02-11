#!/usr/bin/env python3
import json

with open('strategy_v1/workflows/sentiment-analysis-hybrid.json', 'r') as f:
    data = json.load(f)

# Find FinBERT_Batch_Analyze and update it
for node in data['nodes']:
    if node.get('name') == 'FinBERT_Batch_Analyze':
        node['parameters']['responseOnly'] = False
        break

# Find or update Prepare_for_FinBERT to ensure it outputs articles
for node in data['nodes']:
    if node.get('name') == 'Prepare_for_FinBERT':
        js = node['parameters'].get('jsCode', '')
        if 'articles' not in js:
            node['parameters']['jsCode'] = """const articles = $input.all();
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

# Add Merge node if not exists
merge_exists = any(n.get('name') == 'Merge_FinBERT_Data' for n in data['nodes'])
if not merge_exists:
    merge_node = {
        "parameters": {
            "jsCode": """const httpResponse = $json;
const preparePrevious = $input.first();

const articles = preparePrevious.json?.articles || [];

return {
  json: {
    ...httpResponse,
    articles: articles
  }
};"""
        },
        "id": "merge-finbert-data-abc123",
        "name": "Merge_FinBERT_Data",
        "type": "n8n-nodes-base.code",
        "position": [7000, 3360],
        "typeVersion": 2,
        "alwaysOutputData": True
    }
    data['nodes'].append(merge_node)
    
    # Update connections
    if 'FinBERT_Batch_Analyze' in data['connections']:
        data['connections']['FinBERT_Batch_Analyze']['main'] = [[{"node": "Merge_FinBERT_Data", "type": "main", "index": 0}]]
    
    if 'Merge_FinBERT_Data' not in data['connections']:
        data['connections']['Merge_FinBERT_Data'] = {}
    data['connections']['Merge_FinBERT_Data']['main'] = [[{"node": "Format_for_GPT4", "type": "main", "index": 0}]]

with open('strategy_v1/workflows/sentiment-analysis-hybrid.json', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Workflow updated")
