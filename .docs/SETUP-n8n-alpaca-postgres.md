# План настройки n8n + Alpaca + PostgreSQL

## 1. Alpaca Custom Auth (HTTP Custom Auth)

1. Открой n8n → Settings → Credentials.
2. Найди созданный credential типа **HTTP Custom Auth** (для Alpaca).
3. Открой его и включи режим `Use json to specify authentication values for headers, body and qs`.
4. В поле JSON вставь:

```json
{
  "headers": {
    "APCA-API-KEY-ID": "PKTOC53GU3GKTQPBLW6YKD23TQ",
    "APCA-API-SECRET-KEY": "3dGsneqVn68341B9aZzrAidUJBcqcgHF9s5EjdbZU974"
  },
  "qs": {},
  "body": {}
}
```

5. Сохрани credential, назови его, например, `Alpaca API Custom`.

---

## 2. PostgreSQL Credential (`PostgreSQL Trading`)

1. В n8n: Settings → Credentials → Add → **Postgres**.
2. Параметры:
   - Host: `***REMOVED***`
   - Port: `5432`
   - Database: `trading_bot`
   - User: `n8n_user`
   - Password: `***REMOVED***`
   - SSL: Off (локальная сеть)
3. Название: `PostgreSQL Trading`.
4. Нажми **Test**, убедись, что соединение успешно.

---

## 3. Telegram Bot Credential

1. Создай бота у `@BotFather` → получи токен.
2. Напиши боту любое сообщение.
3. Получи chat id:
   - Открой в браузере: `https://api.telegram.org/bot<ТОКЕН>/getUpdates`
   - Найди `"chat":{"id":...}` — это твой chat id.
4. В n8n: Settings → Credentials → Add → **Telegram**.
5. Вставь токен бота, сохрани credential.

---

## 4. Импорт основного workflow

1. В n8n: Workflows → Import from File.
2. Выбери файл `n8n/workflows/ema-crossover-bot.json` из репозитория.
3. После импорта открой workflow в редакторе.

---

## 5. Привязка credentials к нодам

1. **Get OHLC Bars**:
   - `Authentication`: `Generic Credential Type`.
   - `Generic Auth Type`: `HTTP Custom Auth` (или как называется у тебя).
   - Credential: выбери `Alpaca API Custom`.

2. **Place Buy Order** и **Close Position**:
   - Аналогично: `Authentication: Generic Credential Type` → `HTTP Custom Auth` → `Alpaca API Custom`.

3. **Log to PostgreSQL** (нода `Log to PostgreSQL`):
   - В поле Credentials выбери `PostgreSQL Trading`.

4. **Telegram Alert**:
   - Выбери твой Telegram credential.
   - В поле `chatId` замени `YOUR_CHAT_ID` на реальный ID из шага 3.

---

## 6. Быстрая проверка (ручной запуск)

1. Открой ноду **Schedule Trigger** и **отключи активацию** workflow (чтобы он не крутился сам во время теста).
2. По цепочке запускай ноды `Execute Node`:
   - `Get OHLC Bars` — убедись, что приходят бары от Alpaca.
   - `Calculate EMA` — проверь, что в output есть `ema5`, `ema20`, `current.close`.
   - `Detect Signal` — посмотри значение `action` (`hold` / `buy` / `sell`).
3. Если `action = buy` или `sell`, проверь:
   - Проходит ли запрос в Alpaca (ордер виден в Paper Dashboard).
   - Появляется ли запись в таблице `trades` в PostgreSQL.
   - Приходит ли сообщение в Telegram.

---

## 7. Автоматический режим (боевой запуск)

1. В **Schedule Trigger** оставь интервал, например, `Every 1 minute`.
2. Активируй workflow (toggle ON / Activate).
3. Наблюдай в течение нескольких дней:
   - Telegram-алерты.
   - Таблица `trades` в БД (`SELECT * FROM trades ORDER BY timestamp DESC LIMIT 20;`).
   - Позиции и сделки в Alpaca Paper.

---

## 8. Настройка параметров стратегии

Параметры можно менять либо в коде ноды `Calculate EMA`, либо в файле `config/settings.json` (если дальше решим подтягивать их из файла).

Рекомендуемые стартовые значения:
- `symbol`: `"NVDA"` или другой ликвидный тикер.
- `timeframe`: `"1Hour"`.
- `confirmationPercent`: `0.75`.
- Размер позиции: 1–5 акций на первые тесты.

После стабильной работы в Paper-режиме можно думать о переносе логики на real account (меняя endpoint Alpaca и ключи).