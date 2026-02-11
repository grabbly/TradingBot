
# Trading Bot v2.0 — Короткая версия (200–250 строк)

**Дата:** Февраль 2026  
**Статус:** Production Ready ✅  
**Цель:** новости + соцсигналы + тех.индикаторы → решение → ордера

---

## 1) Что делает система (1 абзац)
Мы каждые 4 часа собираем новости (EODHD + Finnhub) и Reddit, обрабатываем их FinBERT, считаем EMA/RSI/Volume каждую минуту и **раз в день в 18:00 EST** (только Пн–Пт) отбираем акции по техфильтрам и риск-правилам, после чего отправляем bracket-ордера в Alpaca и алерты в Telegram.

---

## 2) Главный Flow (очень коротко)
1. **News + Social (каждые 4 часа)** → `news_articles`
2. **Sentiment Analysis (каждые 4 часа)** → `sentiment_scores`
3. **EMA Logger (каждую минуту)** → `ema_snapshots`
4. **Sentiment Executor (18:00 EST, Пн–Пт)** → `positions`, `account_balance`, Alpaca orders

---

## 3) Где участвуют EMA данные
**EMA Logger** (каждую минуту) пишет `ema_snapshots` → **Sentiment Executor** читает последнюю запись и применяет 4 фильтра:
- **price > EMA200** (обязательный)
- **EMA9 > EMA21** (обязательный)
- **RSI14 < 70** (обязательный)
- **volume > volume_ma20** (обязательный)

Если все 4 условия TRUE → генерируется BUY сигнал.

---

## 4) Важные правила риска
- **1% риск на сделку**
- **Stop Loss 2% / Take Profit 4%**
- **Максимум 4 позиции**, максимум **2 в секторе**
- **Drawdown ≥ 10% → остановка торговли**

---

## 5) Тайминг запуска
- **EMA Logger:** каждую минуту (24/7)
- **News Collector:** каждые 4 часа
- **Social Collector:** каждые 4 часа
- **Sentiment Analysis:** каждые 4 часа
- **Sentiment Executor:** 18:00 EST, Пн–Пт

---

## 6) Источники данных (минимум)
- **EODHD** — новости компаний
- **Finnhub** — компания‑центричные новости (fallback)
- **Reddit** — соцсигналы
- **Alpaca Data** — OHLCV бары

---

## 7) Базы данных: что где хранится
- `news_articles` — новости/посты (неанализированные и анализированные)
- `sentiment_scores` — ежедневный скор по тикеру
- `ema_snapshots` — минутные EMA/RSI/Volume
- `positions` — открытые/закрытые позиции
- `account_balance` — equity, cash, drawdown

---

## 8) Мини‑диаграмма
```
News + Reddit (4h) ──→ news_articles ──→ FinBERT ──→ sentiment_scores
EMA Logger (1m) ─────→ ema_snapshots ──────────────┐
                                                   ├─→ Sentiment Executor (18:00 EST) → Alpaca + DB + Telegram
                                                   └─→ Dashboard
```

---

## 8.1) Flow нодов (workflow процессы)
**News Collector:**
Trigger → For Each Symbol → Fetch EODHD → (Empty?) → Fetch Finnhub → Normalize → DB Insert → Done

**Social Collector:**
Trigger → For Each Symbol → Fetch Reddit → Filter/Normalize → DB Insert → Done

**Sentiment Analysis:**
Trigger → Load Unanalyzed Articles → Batch by Symbol → FinBERT → Aggregate Score → DB Insert → Mark Analyzed → Done

**EMA Logger:**
Trigger → Fetch Alpaca Bars → For Each Symbol → Calc EMA/RSI/Volume → Detect Crossover → DB Insert → Done

**Sentiment Executor:**
Trigger → Drawdown Gate → Macro Gate → For Each Symbol → Load EMA + Sentiment → Tech Filters → Sector/Limit Check → Size Position → Alpaca Order → DB Log → Telegram Alert → Done

---

## 9) Что важно для BUY сигнала (коротко)
- **Trend:** price > EMA200
- **Momentum:** EMA9 > EMA21 (Golden Cross)
- **Overbought check:** RSI14 < 70
- **Volume confirmation:** volume > volume_ma20
- **Risk rules:** 1% риск, 2% SL, 4% TP, 4 позиции макс

---

## 10) Список отслеживаемых тикеров
- AAPL
- NVDA
- TSLA
- GOOGL
- MSFT
- AMZN
- META

---

## 11) Компоненты системы (минимум)
- **n8n** — оркестрация workflow
- **PostgreSQL** — хранение данных
- **Alpaca** — paper trading
- **FinBERT** — sentiment анализ
- **Telegram** — алерты
- **Flask + Nginx** — dashboard

---

## 12) Что проверить перед запуском
- n8n и PostgreSQL запущены
- таблицы есть: `news_articles`, `sentiment_scores`, `ema_snapshots`, `positions`, `account_balance`
- API keys заданы (Alpaca, Finnhub, EODHD, HuggingFace, Telegram)
- все 5 workflow активны

---

## 13) Операционный минимум (очень коротко)
- В 17:00 EST убедиться, что `ema_snapshots` обновляется
- В 18:00 EST Sentiment Executor отработал без ошибок
- После 18:00 EST Telegram алерт пришел

---

## 14) Типичные ошибки (1 строка каждая)
- **Нет EMA данных** → проблема с Alpaca Data API
- **Нет sentiment_scores** → FinBERT не отработал
- **Нет Telegram** → неверный токен или chat_id
- **Trading halted** → drawdown ≥ 10%

---

## 15) Мини‑пример сигнала (1 строка)
Если **price > EMA200** и **EMA9 > EMA21** и **RSI14 < 70** и **volume > volume_ma20** → BUY.

---

## 16) Роли и ответственность (кто за что)
- **Сбор новостей:** News Collector
- **Сбор соцсигналов:** Social Collector
- **Техиндикаторы:** EMA Logger
- **Сентимент:** Sentiment Analysis
- **Торговля:** Sentiment Executor

---

## 17) Важные ограничения
- Торговля **paper** (без реальных денег)
- Даты FOMC/earnings должны быть заполнены
- Финальная логика работает только в будни

---

## 18) Мини‑чеклист запуска (6 пунктов)
1. PostgreSQL жив
2. n8n жив
3. EMA Logger пишет
4. News/Social collectors пишут
5. Sentiment scores обновляются
6. Executor запустился в 18:00

---

## 19) Алерты (что приходит)
- BUY / SELL
- Drawdown halt
- Macro skip (если включены даты)
- Extreme sentiment
- Ошибка workflow

---

## 20) Что делать дальше
- 1–2 недели paper‑теста
- Калибровка фильтров
- Потом — переход на real

---

## 21) Короткий контроль качества
- **EMA:** минимум 1 запись/мин/символ
- **News:** минимум 10 статей/день на тикер
- **Sentiment:** 1 скор/день/тикер
- **Executor:** 1 запуск/день

---

## 22) Полезные заметки
- EMA200 фильтрует тренд
- EMA9>EMA21 — вход по импульсу
- RSI<70 защищает от перекупленности
- Volume>MA20 подтверждает движение

---

## 23) Кратко про риски
- 1% риск на сделку ограничивает просадку
- SL 2% фиксирует убыток рано
- TP 4% дает математику 2:1

---

## 24) Сводка одной строкой
**Система читает новости + считает EMA → фильтрует по риску → отправляет ордера.**

---


