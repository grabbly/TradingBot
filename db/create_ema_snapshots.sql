-- Создание таблицы для снапшотов EMA
-- Запустить на сервере: sudo -u postgres psql -d trading_bot -f create_ema_snapshots.sql

CREATE TABLE IF NOT EXISTS ema_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    close_price DECIMAL(12, 4) NOT NULL,
    ema5 DECIMAL(12, 4),
    ema8 DECIMAL(12, 4),
    ema9 DECIMAL(12, 4),
    ema13 DECIMAL(12, 4),
    ema20 DECIMAL(12, 4),
    ema21 DECIMAL(12, 4),
    ema34 DECIMAL(12, 4),
    ema50 DECIMAL(12, 4),
    ema100 DECIMAL(12, 4),
    ema200 DECIMAL(12, 4),
    rsi14 DECIMAL(12, 4),
    volume DECIMAL(18, 4),
    volume_ma20 DECIMAL(18, 4),
    action VARCHAR(20),         -- 'hold', 'buy', 'sell', и т.п.
    crossover VARCHAR(10),      -- 'bullish', 'bearish', 'none'
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_ema_snapshots_symbol ON ema_snapshots(symbol);
CREATE INDEX IF NOT EXISTS idx_ema_snapshots_timestamp ON ema_snapshots(timestamp DESC);

-- Права для n8n_user
GRANT SELECT, INSERT, UPDATE, DELETE ON ema_snapshots TO n8n_user;
GRANT USAGE, SELECT ON SEQUENCE ema_snapshots_id_seq TO n8n_user;

SELECT 'ema_snapshots table created successfully' AS status;
