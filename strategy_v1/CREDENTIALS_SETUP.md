# Настройка Credentials для n8n

## 1. Alpaca API

### Получение ключей
1. Зарегистрируйся на [alpaca.markets](https://alpaca.markets)
2. Перейди в Dashboard → Paper Trading → API Keys
3. Сгенерируй новый ключ

### Настройка в n8n
1. Settings → Credentials → Add Credential
2. Выбери **Header Auth**
3. Создай credential с именем `Alpaca API`
4. Добавь два заголовка:

| Name | Value |
|------|-------|
| APCA-API-KEY-ID | `твой_api_key` |
| APCA-API-SECRET-KEY | `твой_secret_key` |

---

## 2. Telegram Bot

### Создание бота
1. Напиши [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь `/newbot` и следуй инструкциям
3. Получи токен бота

### Получение Chat ID
1. Напиши своему боту любое сообщение
2. Открой: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Найди `"chat":{"id":123456789}` — это твой Chat ID

### Настройка в n8n
1. Settings → Credentials → Add Credential
2. Выбери **Telegram API**
3. Вставь токен бота

---

## 3. PostgreSQL

### Инициализация базы данных

```bash
# 1. Создать пользователя и базу (от postgres superuser)
psql -h your_postgres_host -U postgres -f db/init.sql

# 2. Применить схему таблиц
psql -h your_postgres_host -U n8n_user -d trading_bot -f db/schema.sql
```

### Настройка в n8n
1. Settings → Credentials → Add Credential
2. Выбери **Postgres**
3. Создай credential с именем `PostgreSQL Trading`
4. Заполни:

| Поле | Значение |
|------|----------|
| Host | `your_postgres_host` |
| Port | `5432` |
| Database | `trading_bot` |
| User | `n8n_user` |
| Password | `your_secure_password` |
| SSL | Отключено (локальная сеть) |

---

## 4. Обновление Workflow

После настройки credentials:
1. Импортируй `ema-crossover-bot.json` в n8n
2. В ноде **Telegram Alert** замени `YOUR_CHAT_ID` на свой
3. Проверь подключение PostgreSQL

---

## Проверка подключения

### Alpaca API
```bash
curl -H "APCA-API-KEY-ID: YOUR_KEY" \
     -H "APCA-API-SECRET-KEY: YOUR_SECRET" \
     https://paper-api.alpaca.markets/v2/account
```

### Alpaca Market Data
```bash
curl -H "APCA-API-KEY-ID: YOUR_KEY" \
     -H "APCA-API-SECRET-KEY: YOUR_SECRET" \
     "https://data.alpaca.markets/v2/stocks/NVDA/bars?timeframe=1Hour&limit=5"
```

### PostgreSQL
```bash
psql -h your_postgres_host -U n8n_user -d trading_bot -c "SELECT * FROM trades LIMIT 5;"
```
