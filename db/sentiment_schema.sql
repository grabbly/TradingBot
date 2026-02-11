-- Sentiment Analysis Database Schema
-- Tables for news-based trading strategy

-- News articles pool
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) UNIQUE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    source VARCHAR(100),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed BOOLEAN DEFAULT FALSE,
    UNIQUE(article_id, symbol)
);

CREATE INDEX idx_news_symbol ON news_articles(symbol);
CREATE INDEX idx_news_published ON news_articles(published_at);
CREATE INDEX idx_news_analyzed ON news_articles(analyzed);

-- Sentiment scores
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    sentiment_score DECIMAL(5,4) NOT NULL,  -- -1.0000 to 1.0000
    rationale TEXT,
    article_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date, symbol)
);

CREATE INDEX idx_sentiment_date ON sentiment_scores(date);
CREATE INDEX idx_sentiment_symbol ON sentiment_scores(symbol);
CREATE INDEX idx_sentiment_score ON sentiment_scores(sentiment_score);

-- Account balance tracking
CREATE TABLE IF NOT EXISTS account_balance (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    balance DECIMAL(12,2) NOT NULL,
    change DECIMAL(10,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_balance_date ON account_balance(date);

-- Trading positions
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    order_type VARCHAR(10) NOT NULL,  -- 'buy' or 'sell'
    value DECIMAL(12,2) NOT NULL,
    sentiment_score DECIMAL(5,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_positions_date ON positions(date);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- Stock symbols to track
CREATE TABLE IF NOT EXISTS tracked_symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),
    sector VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Initial symbols
INSERT INTO tracked_symbols (symbol, name, sector, active) VALUES
    ('NVDA', 'NVIDIA Corporation', 'Technology', true),
    ('AAPL', 'Apple Inc.', 'Technology', true),
    ('TSLA', 'Tesla Inc.', 'Consumer Discretionary', true),
    ('GOOGL', 'Alphabet Inc.', 'Communication Services', true),
    ('MSFT', 'Microsoft Corporation', 'Technology', true),
    ('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', true),
    ('META', 'Meta Platforms Inc.', 'Communication Services', true)
ON CONFLICT (symbol) DO NOTHING;

COMMENT ON TABLE news_articles IS 'Pool of fetched news articles for sentiment analysis';
COMMENT ON TABLE sentiment_scores IS 'Daily sentiment scores per symbol';
COMMENT ON TABLE account_balance IS 'Daily account balance tracking';
COMMENT ON TABLE positions IS 'All buy/sell orders executed';
COMMENT ON TABLE tracked_symbols IS 'List of stock symbols to analyze';
