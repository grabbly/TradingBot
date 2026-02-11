# EMA Logger Workflow — Детальное Описание Структуры

**Версия:** v2.0 (Batch optimized)  
**Статус:** Production Ready  
**Триггер:** Каждую минуту 24/7  
**Функция:** Сбор OHLCV данных, расчет 10 EMAs + RSI14 + Volume MA20, обнаружение кроссоверов, запись в БД

---

## 📊 Общая Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMA LOGGER WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

[1] Every 1 Minute (Trigger)
        ↓
[2] Load Symbols List
        ↓
[3] Get All OHLC Bars (Batch) ← ОДИН запрос к Alpaca!
        ↓
[4] Split Batch Response
        ↓
[5] For Each Symbol (Loop) ← ЦИКЛ по 7 символам
        ├→ [6] Calculate EMA/RSI/Volume
        ├→ [7] Detect Crossover
        └→ [8] Save to ema_snapshots (× 7 раз)
```

---

## 🔵 NODE 1: Every 1 Minute (Schedule Trigger)

**Тип:** `n8n-nodes-base.scheduleTrigger`  
**ID:** `94de81d1-7713-4f8e-99b9-a8d589b720a6`  
**Позиция:** [4128, 288]

### Параметры
```json
{
  "rule": {
    "interval": [
      {
        "field": "minutes",
        "minutesInterval": 1
      }
    ]
  }
}
```

### Что делает
- **Запускает workflow каждую минуту** 24/7 без остановки
- Не требует внешних данных
- Передает `{}` (пустой объект) следующему узлу

### Выход
```json
{}
```

### Примечание
Это триггер-ноде, через него начинается цепь выполнения. Каждые 60 секунд цепь полностью выполняется.

---

## 🔵 NODE 2: Load Symbols List

**Тип:** `n8n-nodes-base.code`  
**ID:** `a07fd90d-d0e3-4842-8955-97c42e11e3e7`  
**Позиция:** [4336, 288]  
**Language:** JavaScript

### Параметры
```javascript
const symbols = ['AAPL', 'NVDA', 'TSLA', 'GOOGL', 'MSFT', 'AMZN', 'META'];
return symbols.map(s => ({json: {symbol: s}}));
```

### Что делает
- **Генерирует массив объектов** для последующего batch-запроса
- Каждый объект содержит `{symbol: 'TICKER'}`
- Преобразует массив в формат для split-ноды

### Выход
```json
[
  {json: {symbol: "AAPL"}},
  {json: {symbol: "NVDA"}},
  {json: {symbol: "TSLA"}},
  {json: {symbol: "GOOGL"}},
  {json: {symbol: "MSFT"}},
  {json: {symbol: "AMZN"}},
  {json: {symbol: "META"}}
]
```

### Примечание
Логически этот узел не нужен (переработать в будущем). Можно убрать и передавать строку напрямую в Alpaca.

---

## 🟣 NODE 3: Get All OHLC Bars (Batch)

**Тип:** `n8n-nodes-base.httpRequest`  
**ID:** `5103cd86-3116-4c6e-a8e1-72098e02476c`  
**Позиция:** [4528, 288]  
**Метод:** GET  
**Аутентификация:** Alpaca API Custom Auth

### URL
```
https://data.alpaca.markets/v2/stocks/bars
```

### Query Parameters
| Параметр | Значение | Описание |
|----------|----------|---------|
| `symbols` | `AAPL,NVDA,TSLA,GOOGL,MSFT,AMZN,META` | Все 7 символов через запятую |
| `timeframe` | `1Min` | Минутные свечи |
| `limit` | `250` | Последние 250 баров для расчета EMAs |
| `adjustment` | `split` | Учитывать сплиты акций |
| `feed` | `sip` | SIP feed (более надежный) |

### Заголовки (Credentials)
```
APCA-API-KEY-ID: [из n8n credentials]
APCA-API-SECRET-KEY: [из n8n credentials]
```

### Что делает
- **Делает ОДИН HTTP запрос** вместо 7 отдельных
- Получает последние 250 минутных баров для всех символов одновременно
- Использует batch-API Alpaca для оптимизации

### Выход (Успешный)
```json
{
  "bars": {
    "AAPL": {
      "bars": [
        {
          "t": "2026-02-02T15:30:00Z",
          "o": 150.50,
          "h": 151.00,
          "l": 150.20,
          "c": 150.85,
          "v": 1234567
        },
        {...}
      ]
    },
    "NVDA": {
      "bars": [...]
    },
    ...
  }
}
```

### Timeout
30 секунд (достаточно для batch-запроса)

### Важно
- **Credentials ID:** `GMo7eqsdOII9unPE` должен быть настроен в n8n
- **Если запрос падает:** Check API key validity

---

## 🟠 NODE 4: Split Batch Response

**Тип:** `n8n-nodes-base.code`  
**ID:** `split_batch_response`  
**Позиция:** [4720, 288]  
**Language:** JavaScript

### Параметры
```javascript
// Ответ от Alpaca приходит как {AAPL: {bars: [...]}, NVDA: {bars: [...]}, ...}
const barsData = $json.bars || $json;
const symbols = Object.keys(barsData);

// Развернуть в массив объектов для цикла
return symbols.map(symbol => ({
  json: {
    symbol,
    bars: barsData[symbol]?.bars || []
  }
}));
```

### Что делает
- **Парсит batch-ответ** от Alpaca
- **Трансформирует структуру** из `{AAPL: {bars:[...]}, NVDA: {...}}` в `[{symbol: "AAPL", bars:[...]}, ...]`
- **Развернуть для цикла:** каждый символ с его барами как отдельный объект

### Выход
```json
[
  {
    json: {
      symbol: "AAPL",
      bars: [{t: "...", o: 150.50, h: 151.00, l: 150.20, c: 150.85, v: 1234567}, ...]
    }
  },
  {
    json: {
      symbol: "NVDA",
      bars: [{...}, ...]
    }
  },
  {...}
]
```

### Примечание
Критический узел! Если он не парсит правильно, цикл сломается.

---

## 🔴 NODE 5: For Each Symbol (Loop)

**Тип:** `n8n-nodes-base.itemLists`  
**ID:** `9f10500d-bf7e-4889-b465-0e123de5b7dc`  
**Позиция:** [4912, 288]  
**TypeVersion:** 3  
**Mode:** `splitOut`

### Параметры
```json
{
  "mode": "splitOut",
  "options": {}
}
```

### Что делает
- **ЦИКЛ:** Берет входящий массив и пропускает каждый элемент через цепь отдельно
- **7 итераций:** одна для каждого символа
- **Каждая итерация** содержит `{symbol: "TICKER", bars: [...]}`

### Поведение
```
Вход: [
  {json: {symbol: "AAPL", bars: [...]}},
  {json: {symbol: "NVDA", bars: [...]}},
  ...
]

Выход (7 раз подряд):
Итерация 1: {json: {symbol: "AAPL", bars: [...]}}
Итерация 2: {json: {symbol: "NVDA", bars: [...]}}
Итерация 3: {json: {symbol: "TSLA", bars: [...]}}
...
Итерация 7: {json: {symbol: "META", bars: [...]}}
```

### Важно
- `mode: "splitOut"` означает "развернуть массив на элементы"
- Следующие 3 узла (6, 7, 8) выполняются **7 раз** — один раз для каждого символа

---

## 🟢 NODE 6: Calculate EMA/RSI/Volume

**Тип:** `n8n-nodes-base.code`  
**ID:** `81a0c877-e143-46ac-a5e3-13ef20380a4c`  
**Позиция:** [4928, 288]  
**Language:** JavaScript  
**Запускается:** 7 раз (одна итерация на символ)

### Входные данные
```json
{
  "symbol": "AAPL",
  "bars": [
    {t: "2026-02-02T15:30:00Z", o: 150.50, h: 151.00, l: 150.20, c: 150.85, v: 1234567},
    {t: "2026-02-02T15:29:00Z", o: 150.45, h: 150.90, l: 150.15, c: 150.50, v: 1100000},
    ... (250 баров)
  ]
}
```

### Параметры
```javascript
const { symbol, bars } = $json;

// Проверка данных
if (!bars || !bars.length) {
  return { json: { symbol, error: 'No bars returned', notReady: true } };
}

// Функции расчета
function calculateEMA(prices, period) {
  // Wilder's EMA: EMA = (Price - Previous_EMA) × Multiplier + Previous_EMA
  // Multiplier = 2 / (period + 1)
}

function calculateRSI(prices, period = 14) {
  // RSI = 100 - (100 / (1 + RS))
  // RS = Average Gain / Average Loss
}

function calculateSMA(values, period) {
  // SMA = Sum of last N values / N
}

// Извлечение цен и объемов
const closes = bars.map(b => parseFloat(b.c));
const volumes = bars.map(b => parseFloat(b.v));
const last = closes.length - 1;
const prev = closes.length - 2;

// Расчет для текущего момента (last) и предыдущего момента (prev)
const current = { close: closes[last], timestamp: bars[last].t };
const previous = { close: closes[prev] };

// Расчет всех 10 EMAs
const periods = [5, 8, 9, 13, 20, 21, 34, 50, 100, 200];
periods.forEach(p => {
  const emaValues = calculateEMA(closes, p);
  current[`ema${p}`] = emaValues[last];
  previous[`ema${p}`] = emaValues[prev];
});

// Дополнительные индикаторы
current.volume = volumes[last];
current.volume_ma20 = calculateSMA(volumes, 20);
current.rsi14 = calculateRSI(closes, 14);
```

### Что делает
- **Вычисляет 10 EMAs** (5, 8, 9, 13, 20, 21, 34, 50, 100, 200) используя Wilder's метод
- **Вычисляет RSI14** (Relative Strength Index за 14 периодов)
- **Вычисляет Volume MA20** (скользящее среднее объема за 20 периодов)
- **Сравнивает текущее и предыдущее значение** для обнаружения кроссоверов

### Выход
```json
{
  "symbol": "AAPL",
  "timestamp": "2026-02-02T15:30:00Z",
  "current": {
    "close": 150.85,
    "ema5": 150.72,
    "ema8": 150.68,
    "ema9": 150.67,
    "ema13": 150.60,
    "ema20": 150.50,
    "ema21": 150.48,
    "ema34": 150.35,
    "ema50": 150.20,
    "ema100": 149.95,
    "ema200": 149.50,
    "rsi14": 62.3,
    "volume": 1234567,
    "volume_ma20": 1100000
  },
  "previous": {
    "close": 150.50,
    "ema5": 150.65,
    "ema9": 150.60,
    "ema21": 150.48,
    ...
  },
  "lastBar": {...}
}
```

### Сложность
⚠️ **Это сложный узел!** Содержит математику для расчета индикаторов.

---

## 🟡 NODE 7: Detect Crossover

**Тип:** `n8n-nodes-base.code`  
**ID:** `757e99b7-b38b-45fe-ae2c-371230ac0bfb`  
**Позиция:** [5136, 288]  
**Language:** JavaScript  
**Запускается:** 7 раз (одна итерация на символ)

### Входные данные
```json
{
  "symbol": "AAPL",
  "current": {
    "close": 150.85,
    "ema9": 150.67,
    "ema21": 150.48,
    "rsi14": 62.3,
    ...
  },
  "previous": {
    "ema9": 150.60,
    "ema21": 150.48,
    ...
  },
  "timestamp": "2026-02-02T15:30:00Z"
}
```

### Параметры
```javascript
const { symbol, current, previous } = $json;

let crossover = 'NONE';
let action = 'HOLD';
let message = '';

// Golden Cross: EMA9 > EMA21
if (previous.ema9 && previous.ema21 && current.ema9 && current.ema21) {
  // Если раньше EMA9 был <= EMA21, а теперь > EMA21
  if (previous.ema9 <= previous.ema21 && current.ema9 > current.ema21) {
    crossover = 'GOLD_UP';      // Золотой крест (BUY сигнал)
    action = 'BUY_SIGNAL';
    message = `Golden Cross: EMA9=${current.ema9.toFixed(2)} > EMA21=${current.ema21.toFixed(2)}`;
  }
  // Если раньше EMA9 был >= EMA21, а теперь < EMA21
  else if (previous.ema9 >= previous.ema21 && current.ema9 < current.ema21) {
    crossover = 'DEATH_DOWN';   // Смертельный крест (SELL сигнал)
    action = 'SELL_SIGNAL';
    message = `Death Cross: EMA9=${current.ema9.toFixed(2)} < EMA21=${current.ema21.toFixed(2)}`;
  }
}
```

### Что делает
- **Обнаруживает Golden Cross:** когда EMA9 пересекает EMA21 вверх (бычий сигнал)
- **Обнаруживает Death Cross:** когда EMA9 пересекает EMA21 вниз (медвежий сигнал)
- **Классифицирует действие:** BUY_SIGNAL, SELL_SIGNAL или HOLD
- **Генерирует сообщение** с описанием кроссовера

### Выход
```json
{
  "symbol": "AAPL",
  "action": "BUY_SIGNAL",
  "crossover": "GOLD_UP",
  "message": "Golden Cross: EMA9=150.67 > EMA21=150.48",
  "timestamp": "2026-02-02T15:30:00Z",
  "close_price": 150.85,
  "ema5": 150.72,
  "ema9": 150.67,
  "ema21": 150.48,
  "ema200": 149.50,
  "rsi14": 62.3,
  "volume": 1234567,
  "volume_ma20": 1100000
}
```

### Примечание
Этот узел выбирает **2 из 10 EMAs** (EMA9 и EMA21) для торговых сигналов. Остальные 8 EMAs используются для визуализации.

---

## 🟣 NODE 8: Save to ema_snapshots

**Тип:** `n8n-nodes-base.postgres`  
**ID:** `f2bbd529-c686-4738-bfe8-1d7ca35a7cae`  
**Позиция:** [5328, 288]  
**Операция:** `executeQuery`  
**Запускается:** 7 раз (одна итерация на символ)

### SQL Query
```sql
INSERT INTO ema_snapshots (
  timestamp, symbol, close_price,
  ema5, ema8, ema9, ema13, ema20, ema21, ema34, ema50, ema100, ema200,
  rsi14, volume, volume_ma20,
  action, crossover, message
)
VALUES (
  '{{ $json.timestamp }}',
  '{{ $json.symbol }}',
  {{ $json.close_price || 'NULL' }},
  {{ $json.ema5 || 'NULL' }},
  ... (все EMAs),
  '{{ $json.action }}',
  '{{ $json.crossover }}',
  '{{ $json.message }}'
)
ON CONFLICT (timestamp, symbol) DO UPDATE SET
  action = EXCLUDED.action,
  crossover = EXCLUDED.crossover,
  message = EXCLUDED.message;
```

### Что делает
- **Вставляет (INSERT) новую запись** в таблицу `ema_snapshots` для каждого символа
- **19 столбцов данных:** timestamp, symbol, все EMAs, RSI, volume, action, crossover, message
- **Обработка конфликтов:** если запись с таким (timestamp, symbol) уже есть, обновляет action/crossover/message
- **Выполняется 7 раз** — один раз для каждого символа

### Входные данные
```json
{
  "symbol": "AAPL",
  "timestamp": "2026-02-02T15:30:00Z",
  "close_price": 150.85,
  "ema5": 150.72,
  "ema9": 150.67,
  "ema21": 150.48,
  "ema200": 149.50,
  "rsi14": 62.3,
  "volume": 1234567,
  "volume_ma20": 1100000,
  "action": "BUY_SIGNAL",
  "crossover": "GOLD_UP",
  "message": "Golden Cross: EMA9=150.67 > EMA21=150.48"
}
```

### Выход (Success)
```json
{
  "command": "INSERT",
  "rowCount": 1,
  "oid": null,
  "rows": []
}
```

### Credentials
```
Database: gdEjFpQ7Jf6e0OER (Postgres account 2)
Host: 192.168.1.3
Port: 5432
DB: trading_bot
User: n8n_user
```

### Таблица Структура
```sql
CREATE TABLE ema_snapshots (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL,
  symbol VARCHAR(20) NOT NULL,
  close_price DECIMAL(12, 4),
  ema5 DECIMAL(12, 4), ema8 DECIMAL(12, 4), ema9 DECIMAL(12, 4), ...
  ema200 DECIMAL(12, 4),
  rsi14 DECIMAL(12, 4),
  volume BIGINT,
  volume_ma20 DECIMAL(12, 4),
  action VARCHAR(20),
  crossover VARCHAR(10),
  message TEXT,
  
  UNIQUE(timestamp, symbol),
  INDEX idx_symbol (symbol),
  INDEX idx_timestamp (timestamp DESC)
);
```

---

## 📈 Полный Data Flow (в деталях)

```
╔════════════════════════════════════════════════════════════════════════╗
║                         MINUTE-BY-MINUTE FLOW                         ║
╚════════════════════════════════════════════════════════════════════════╝

T=00:00:00
├─ NODE 1: Every 1 Minute → TRIGGER
│
T=00:00:01
├─ NODE 2: Load Symbols List → [{symbol: AAPL}, {symbol: NVDA}, ...]
│
T=00:00:02
├─ NODE 3: Get All OHLC Bars (Batch)
│  └─ REQUEST: GET /v2/stocks/bars?symbols=AAPL,NVDA,...
│  └─ RESPONSE: {AAPL: {bars: [...]}, NVDA: {bars: [...]}, ...}
│
T=00:00:03
├─ NODE 4: Split Batch Response
│  └─ Transform: {AAPL: {...}} → [{symbol: AAPL, bars: [...]}, ...]
│
T=00:00:04
├─ NODE 5: For Each Symbol (LOOP START)
│
│  ┌──── ITERATION 1 (AAPL) ────┐
│  │ T=00:00:05
│  ├─ NODE 6: Calculate EMA/RSI/Volume for AAPL
│  │  └─ Current:  {ema9: 150.67, ema21: 150.48, rsi14: 62.3, ...}
│  │  └─ Previous: {ema9: 150.60, ema21: 150.48, ...}
│  │
│  ├─ NODE 7: Detect Crossover for AAPL
│  │  └─ Check: prev.ema9 <= prev.ema21 && curr.ema9 > curr.ema21?
│  │  └─ Result: YES → action: 'BUY_SIGNAL', crossover: 'GOLD_UP'
│  │
│  ├─ NODE 8: Save to DB (AAPL)
│  │  └─ INSERT INTO ema_snapshots VALUES (AAPL record)
│  │  └─ Status: ✅ 1 row inserted
│  │
│  └─ ITERATION 1 COMPLETE ────┘
│
│  ┌──── ITERATION 2 (NVDA) ────┐
│  │ (repeat nodes 6, 7, 8)
│  │ └─ Calculate → Detect → Save (NVDA)
│  └─ ITERATION 2 COMPLETE ────┘
│
│  ... (ITERATIONS 3-7 for TSLA, GOOGL, MSFT, AMZN, META)
│
│  ┌──── ITERATION 7 (META) ────┐
│  │ (repeat nodes 6, 7, 8)
│  └─ ITERATION 7 COMPLETE ────┘
│
├─ NODE 5: For Each Symbol (LOOP END)
│
T=00:00:30
└─ WORKFLOW COMPLETE
   └─ Result: 7 rows inserted in ema_snapshots
   └─ Ready for next trigger (in 30 seconds)

T=00:01:00
└─ NODE 1: Every 1 Minute → TRIGGER (repeat)
```

---

## ⚡ Производительность

| Метрика | Значение |
|---------|----------|
| **Период запуска** | Каждую минуту |
| **Количество HTTP запросов** | 1 (вместо 7) |
| **Символов обрабатывается** | 7 |
| **EMAs рассчитывается** | 10 × 7 = 70 |
| **Записей в БД** | 7 в минуту |
| **Записей в час** | 420 |
| **Записей в день** | ~10,000 |
| **Ожидаемое время выполнения** | 20-30 сек |

---

## 🛠️ Troubleshooting

| Ошибка | Причина | Решение |
|--------|--------|---------|
| **NODE 3 падает (timeout)** | Alpaca API недоступен | Check network, API key |
| **NODE 4 парсит неправильно** | Неверный формат ответа | Log $json, проверить структуру |
| **NODE 6 возвращает NULL EMA** | Недостаточно баров | Увеличить limit или добавить fallback |
| **NODE 8 ошибка CONFLICT** | timestamp + symbol duplicate | Нормально (UPDATE срабатывает) |
| **NODE 8 INSERT fails** | DB не доступна | Check PostgreSQL connection |

---

## 📋 Checklist перед запуском

- [ ] Alpaca credentials в n8n (ID: `GMo7eqsdOII9unPE`)
- [ ] PostgreSQL запущена и доступна
- [ ] Таблица `ema_snapshots` создана с индексами
- [ ] n8n credentials для PostgreSQL сконфигурированы
- [ ] Workflow активен (не disabled)
- [ ] Символы в NODE 2 актуальны
- [ ] Параметры batch-запроса верны (timeframe, limit)

---

**Документ создан:** 2 февраля 2026  
**Версия workflow:** EMA Logger v2.0 (Batch optimized)  
**Последнее обновление:** Исправлена архитектура с циклом For Each
