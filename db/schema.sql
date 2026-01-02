-- Схема базы данных для Trading Bot
-- PostgreSQL

-- Таблица сделок
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'buy', 'sell', 'signal_detected', 'signal_cancelled'
    price DECIMAL(12, 4),
    quantity INTEGER,
    ema5 DECIMAL(12, 4),
    ema20 DECIMAL(12, 4),
    crossover VARCHAR(10),  -- 'bullish', 'bearish', 'none'
    message TEXT,
    order_id VARCHAR(100),
    pnl_percent DECIMAL(8, 4)
);

-- Таблица состояния бота
CREATE TABLE IF NOT EXISTS bot_state (
    id INTEGER PRIMARY KEY DEFAULT 1,
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'flat',  -- 'flat', 'waiting_confirmation', 'in_position'
    crossover_price DECIMAL(12, 4),
    crossover_time TIMESTAMPTZ,
    entry_price DECIMAL(12, 4),
    entry_time TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT single_row CHECK (id = 1)
);

-- Инициализация состояния
INSERT INTO bot_state (symbol, status) 
VALUES ('NVDA', 'flat')
ON CONFLICT (id) DO NOTHING;

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_action ON trades(action);

-- View для статистики по символу
CREATE OR REPLACE VIEW trade_stats AS
SELECT 
    symbol,
    COUNT(*) FILTER (WHERE action = 'buy') as total_buys,
    COUNT(*) FILTER (WHERE action = 'sell') as total_sells,
    AVG(pnl_percent) FILTER (WHERE action = 'sell') as avg_pnl,
    SUM(pnl_percent) FILTER (WHERE action = 'sell') as total_pnl,
    MAX(timestamp) as last_trade
FROM trades
GROUP BY symbol;
