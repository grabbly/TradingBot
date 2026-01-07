#!/bin/bash
# Установка и запуск Treddy Chart Service на сервере ***REMOVED***
# ВНИМАНИЕ: Ничего не сломает — создаёт новый сервис на порту 5001

set -e

echo "=== Установка Treddy Chart Service ==="

# 1. Копируем папку web на сервер
echo "Шаг 1: Копирование файлов..."
rsync -avz --delete \
  /Users/gabby/git/TradingBot/web/ \
  gabby@***REMOVED***:/home/gabby/TradingBot/web/

# 2. На сервере: создаём venv и устанавливаем зависимости
echo "Шаг 2: Установка Python зависимостей..."
ssh gabby@***REMOVED*** << 'REMOTE_SCRIPT'
cd /home/gabby/TradingBot/web
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Python зависимости установлены"
REMOTE_SCRIPT

# 3. Копируем systemd service
echo "Шаг 3: Настройка systemd service..."
ssh gabby@***REMOVED*** << 'REMOTE_SCRIPT'
sudo cp /home/gabby/TradingBot/web/treddy.service /etc/systemd/system/treddy.service
sudo systemctl daemon-reload
sudo systemctl enable treddy.service
sudo systemctl start treddy.service
sudo systemctl status treddy.service --no-pager
echo "Сервис treddy запущен"
REMOTE_SCRIPT

# 4. Копируем nginx config
echo "Шаг 4: Настройка nginx..."
ssh gabby@***REMOVED*** << 'REMOTE_SCRIPT'
sudo cp /home/gabby/TradingBot/web/nginx-treddy.conf /etc/nginx/sites-available/treddy
sudo ln -sf /etc/nginx/sites-available/treddy /etc/nginx/sites-enabled/treddy
sudo nginx -t
sudo systemctl reload nginx
echo "Nginx настроен"
REMOTE_SCRIPT

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Проверь:"
echo "  - http://treddy.acebox.eu/"
echo "  - http://***REMOVED***:5001/health (локально)"
echo ""
echo "Логи сервиса:"
echo "  sudo journalctl -u treddy -f"
echo ""
echo "Управление:"
echo "  sudo systemctl status treddy"
echo "  sudo systemctl restart treddy"
echo "  sudo systemctl stop treddy"
