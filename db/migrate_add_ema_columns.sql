-- DEPRECATED: Этот файл устарел
-- Используйте вместо него: db/migrations/001_add_ema_columns.sql
-- 
-- Система миграций теперь находится в папке db/migrations/
-- Подробнее: db/MIGRATIONS.md

-- Миграция: добавление новых колонок EMA
-- Добавляем колонки для EMA: 8, 9, 13, 21, 34, 50, 100, 200

-- Обновляем таблицу ema_snapshots
ALTER TABLE ema_snapshots 
ADD COLUMN IF NOT EXISTS ema8 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema9 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema13 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema21 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema34 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema50 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema100 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema200 DECIMAL(12, 4);

-- Обновляем таблицу trades
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS ema8 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema9 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema13 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema21 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema34 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema50 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema100 DECIMAL(12, 4),
ADD COLUMN IF NOT EXISTS ema200 DECIMAL(12, 4);

-- Проверка структуры таблицы ema_snapshots
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ema_snapshots' 
ORDER BY ordinal_position;

-- Проверка структуры таблицы trades
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'trades' 
ORDER BY ordinal_position;
