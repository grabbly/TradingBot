#!/bin/bash

# Скрипт для проверки таблицы positions в PostgreSQL
# Connection info: Host 192.168.1.3, Database trading_bot

echo "=== Checking positions table on 192.168.1.3 ==="
echo ""
echo "Method 1: Last 20 orders"
ssh gabby@192.168.1.3 "sudo -u postgres psql -d trading_bot -c 'SELECT date, symbol, order_type, value, created_at FROM positions ORDER BY created_at DESC LIMIT 20;'"

echo ""
echo "Method 2: Summary by order type"
ssh gabby@192.168.1.3 "sudo -u postgres psql -d trading_bot -c 'SELECT COUNT(*) as total_orders, order_type, COUNT(DISTINCT symbol) as unique_symbols, SUM(value) as total_value FROM positions GROUP BY order_type;'"

echo ""
echo "Method 3: Today orders only"
ssh gabby@192.168.1.3 "sudo -u postgres psql -d trading_bot -c \"SELECT * FROM positions WHERE date = CURRENT_DATE ORDER BY created_at DESC;\""

echo ""
echo "=== Database Connection Info ==="
echo "Host: 192.168.1.3"
echo "Database: trading_bot"
echo "User: postgres (via sudo)"
echo "Table: positions"

