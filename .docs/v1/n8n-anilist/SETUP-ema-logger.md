# EMA Logger Workflow — Инструкция по настройке

## Что это

Отдельный workflow **только для сбора данных** — без покупок и продаж.  
Каждые 5 минут он:
1. Получает бары с Alpaca (NVDA, 1 час, 50 последних свечей).
2. Считает EMA 5 и EMA 20.
3. Определяет crossover и action (hold/buy/sell) — **но не размещает ордера**.
4. Пишет снапшот (timestamp, symbol, close_price, ema5, ema20, action, crossover, message) в таблицу `ema_snapshots`.

---

## Шаг 1: Создать таблицу ema_snapshots

На сервере Postgres (`***REMOVED***`):

```bash
ssh gabby@***REMOVED***
sudo -u postgres psql -d trading_bot -f /path/to/TradingBot/db/create_ema_snapshots.sql
```

Или вручную:

```sql
sudo -u postgres psql -d trading_bot

CREATE TABLE IF NOT EXISTS ema_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    close_price DECIMAL(12, 4) NOT NULL,
    ema5 DECIMAL(12, 4),
    ema20 DECIMAL(12, 4),
    action VARCHAR(20),
    crossover VARCHAR(10),
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_ema_snapshots_symbol ON ema_snapshots(symbol);
CREATE INDEX IF NOT EXISTS idx_ema_snapshots_timestamp ON ema_snapshots(timestamp DESC);

GRANT SELECT, INSERT, UPDATE, DELETE ON ema_snapshots TO n8n_user;
GRANT USAGE, SELECT ON SEQUENCE ema_snapshots_id_seq TO n8n_user;
```

---

## Шаг 2: Импортировать workflow в n8n

1. Открой n8n → Workflows → **Import from File**.
2. Выбери `n8n/workflows/ema-logger.json`.
3. После импорта проверь ноды:
   - **Get OHLC Bars**: должен быть привязан к credential `Auth Alpaca API` (HTTP Custom Auth).
   - **Log Snapshot to DB**: должен быть привязан к `PostgreSQL Trading`.

---

## Шаг 3: Ручной тест

1. Открой workflow "EMA Logger (Data Collection)".
2. **Не активируй** его сразу — протестируй вручную:
   - Execute Node на `Get OHLC Bars` — должны прийти бары.
   - Execute Node на `Calculate EMA` — должны появиться `ema5`, `ema20`, `current.close`.
   - Execute Node на `Detect Signal` — должен быть `action`, `crossover`, `message`.
   - Execute Node на `Log Snapshot to DB` — проверь, что запись добавилась:

     ```sql
     SELECT * FROM ema_snapshots ORDER BY timestamp DESC LIMIT 5;
     ```

---

## Шаг 4: Активировать

1. В ноде **Every 5 Minutes** можно поменять интервал (например, 1 минута для быстрого набора данных).
2. Активируй workflow (toggle ON).
3. Дай ему поработать 1–2 часа, чтобы накопились данные.

---

## Шаг 5: Визуализация

### Вариант 1: Python-скрипт

```bash
cd TradingBot
python3 -m pip install psycopg2-binary matplotlib
PGPASSWORD=***REMOVED*** python scripts/plot_ema.py --symbol NVDA --days 1 --output nvda_ema.png
```

График сохранится в `nvda_ema.png`.

### Вариант 2: Metabase / Grafana

- Подключи Metabase или Grafana к БД `trading_bot` на `***REMOVED***:5432`.
- Создай time-series график:
  - X: `timestamp`
  - Y: три линии — `close_price`, `ema5`, `ema20`

---

## Что дальше

Когда накопится достаточно данных и увидишь, что стратегия работает адекватно на графиках:
- Можно вернуться к основному workflow `ema-crossover-bot.json` и активировать покупки/продажи (сначала с маленьким размером позиции).
