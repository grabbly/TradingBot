# Treddy Web Dashboard

Простой веб-интерфейс для визуализации EMA-графиков из PostgreSQL.

## Архитектура

- **Flask** приложение на порту `5001` (локально).
- **Nginx** проксирует `treddy.acebox.eu` → `127.0.0.1:5001`.
- **Gunicorn** для production-запуска Flask.
- **Systemd** service для автозапуска.

## Файлы

```
web/
├── app.py                   # Flask приложение
├── templates/
│   └── index.html          # Dashboard UI
├── requirements.txt        # Python зависимости
├── treddy.service         # Systemd service
├── nginx-treddy.conf      # Nginx конфиг
└── deploy.sh              # Скрипт автоматической установки
```

## Установка

**Из локального Mac:**

```bash
cd /Users/gabby/git/TradingBot
./web/deploy.sh
```

**Пароль sudo на сервере:** `2356HJK`

Скрипт:
1. Скопирует все файлы на сервер ***REMOVED***.
2. Создаст venv и установит зависимости.
3. Настроит systemd service `treddy`.
4. Настроит nginx для домена `treddy.acebox.eu`.
5. Запустит сервис.

## Ручная установка (если нужно)

```bash
# На сервере ***REMOVED***
cd /home/gabby/TradingBot/web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Тест локально
python app.py
# Открой http://***REMOVED***:5001

# Установка systemd service
sudo cp treddy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable treddy
sudo systemctl start treddy

# Установка nginx
sudo cp nginx-treddy.conf /etc/nginx/sites-available/treddy
sudo ln -s /etc/nginx/sites-available/treddy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Использование

Открой в браузере:
- **http://treddy.acebox.eu** (если DNS настроен)
- **http://***REMOVED***:5001** (локально на сервере)

Dashboard:
- Выбор символа (NVDA, AAPL, и т.д.)
- Период: 1, 3, 7, 14, 30 дней
- Auto-refresh каждые 60 секунд
- График: Close, EMA 5, EMA 20

## API Endpoints

- `GET /` — главная страница с UI
- `GET /chart/<symbol>.png?days=7` — PNG график
- `GET /api/data/<symbol>?days=7` — JSON данные
- `GET /health` — health check

## Управление

```bash
# Статус
sudo systemctl status treddy

# Рестарт
sudo systemctl restart treddy

# Логи
sudo journalctl -u treddy -f

# Остановка
sudo systemctl stop treddy
```

## Безопасность

- Сервис слушает **только 127.0.0.1:5001** (не виден извне).
- Nginx проксирует трафик с домена.
- Systemd запускает от пользователя `gabby` (не root).
- Пароль БД передаётся через переменные окружения systemd.

## Что НЕ сломается

- Существующие nginx-конфиги (`dma-api`, `girlsandblocks`) не затронуты.
- Порт 5001 свободен (не конфликтует с 80, 443, 3001).
- PostgreSQL не изменяется (только читаем `ema_snapshots`).
- n8n не затронут.

## Обновление кода

```bash
# Из Mac
cd /Users/gabby/git/TradingBot
./web/deploy.sh
```

Или только код без перезапуска service:

```bash
rsync -avz web/ gabby@***REMOVED***:/home/gabby/TradingBot/web/
ssh gabby@***REMOVED*** "sudo systemctl restart treddy"
```

## Требования

- Python 3.12+
- PostgreSQL с таблицей `ema_snapshots`
- Nginx
- Домен `treddy.acebox.eu` должен быть направлен на ***REMOVED***
