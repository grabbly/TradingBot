-- Migration 002: Add sector to tracked_symbols
-- Date: 2026-02-01

ALTER TABLE tracked_symbols
ADD COLUMN IF NOT EXISTS sector VARCHAR(50);

-- Seed sectors for existing symbols
UPDATE tracked_symbols SET sector = 'Technology' WHERE symbol IN ('AAPL','MSFT','NVDA');
UPDATE tracked_symbols SET sector = 'Communication Services' WHERE symbol IN ('GOOGL','META');
UPDATE tracked_symbols SET sector = 'Consumer Discretionary' WHERE symbol IN ('AMZN','TSLA');
