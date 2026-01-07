# Database Migrations - Руководство

Система управления миграциями базы данных для TradingBot.

## 📋 Что это?

Миграции позволяют версионировать изменения схемы базы данных и применять их автоматически.

## 🏗️ Структура

```
db/
├── migrations/              # Папка с миграциями
│   ├── 000_init_schema_migrations.sql
│   ├── 001_add_ema_columns.sql
│   └── README.md
├── apply_migrations.sh      # Bash скрипт для применения
├── schema.sql              # Базовая схема (для новой БД)
└── init.sql                # Инициализация (для новой БД)
```

## 🚀 Способы применения миграций

### Способ 1: N8N Workflow (Рекомендуется)

1. Открыть n8n UI
2. Импортировать: `n8n/workflows/db-migrate.json`
3. Запустить workflow вручную
4. Проверить результат в Summary

**Преимущества:**
- ✅ Визуальный интерфейс
- ✅ Автоматическая проверка применённых миграций
- ✅ Логирование результатов
- ✅ Безопасное применение (пропускает уже применённые)

### Способ 2: Bash скрипт

```bash
cd /Users/gabby/git/TradingBot

# Установить переменные окружения
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=trading_bot
export DB_USER=postgres
export DB_PASSWORD=your_password

# Запустить скрипт
./db/apply_migrations.sh
```

**Преимущества:**
- ✅ Быстрое применение через CLI
- ✅ Автоматическая обработка всех миграций
- ✅ Цветной вывод прогресса
- ✅ Останавливается при ошибке

### Способ 3: Вручную через psql

```bash
# 1. Инициализировать таблицу миграций
psql -h localhost -U postgres -d trading_bot \
  -f db/migrations/000_init_schema_migrations.sql

# 2. Применить миграцию
psql -h localhost -U postgres -d trading_bot \
  -f db/migrations/001_add_ema_columns.sql

# 3. Зарегистрировать миграцию
psql -h localhost -U postgres -d trading_bot -c "
INSERT INTO schema_migrations (version, name) 
VALUES ('001', 'add_ema_columns')
ON CONFLICT (version) DO NOTHING;
"
```

## 📝 Создание новой миграции

### Шаг 1: Создать файл

```bash
# Определить следующий номер (например, 002)
cd db/migrations
touch 002_your_description.sql
```

### Шаг 2: Написать SQL

```sql
-- Миграция 002: Добавление таблицы user_settings
-- Дата: 2026-01-05
-- Описание: Таблица для хранения пользовательских настроек

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, setting_key)
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id 
ON user_settings(user_id);
```

### Шаг 3A: Для N8N - добавить в workflow

Открыть ноду "Check Pending Migrations" в workflow `db-migrate.json`:

```javascript
const migrations = [
  {
    version: '001',
    name: 'add_ema_columns',
    description: 'Добавление колонок EMA',
    sql: `...`
  },
  // Добавить новую миграцию
  {
    version: '002',
    name: 'add_user_settings',
    description: 'Таблица пользовательских настроек',
    sql: `
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, setting_key)
);
    `
  }
];
```

### Шаг 3B: Для Bash - просто создать файл

Скрипт `apply_migrations.sh` автоматически найдёт новый файл.

## 🔍 Проверка статуса

```sql
-- Все применённые миграции
SELECT version, name, applied_at 
FROM schema_migrations 
ORDER BY version;

-- Текущая версия БД
SELECT MAX(version) as current_version 
FROM schema_migrations;

-- Подробная информация
SELECT 
    version,
    name,
    applied_at,
    AGE(NOW(), applied_at) as time_since_applied
FROM schema_migrations 
ORDER BY version DESC;
```

## ⚠️ Важные правила

### ✅ DO (Делать)

1. **Всегда используй IF NOT EXISTS / IF EXISTS**
   ```sql
   ALTER TABLE mytable ADD COLUMN IF NOT EXISTS mycolumn VARCHAR(50);
   ```

2. **Добавляй подробные комментарии**
   ```sql
   -- Миграция 003: Название
   -- Дата: YYYY-MM-DD
   -- Описание: Зачем нужна эта миграция
   -- Связанные issues: #123
   ```

3. **Тестируй на dev окружении**
   ```bash
   # Создать тестовую БД
   createdb trading_bot_test
   # Применить миграции
   DB_NAME=trading_bot_test ./db/apply_migrations.sh
   ```

4. **Версии идут по порядку**
   - 000, 001, 002, 003, ...
   - Не пропускать номера

5. **Идемпотентность**
   - Миграция должна работать повторно без ошибок
   - Использовать IF NOT EXISTS, ON CONFLICT, и т.д.

### ❌ DON'T (Не делать)

1. **НЕ изменяй применённые миграции**
   - Создавай новую миграцию для исправлений

2. **НЕ используй DROP без IF EXISTS**
   ```sql
   -- Плохо ❌
   DROP TABLE mytable;
   
   -- Хорошо ✅
   DROP TABLE IF EXISTS mytable;
   ```

3. **НЕ применяй destructive операции без backup**
   ```bash
   # Сделай backup перед DROP/DELETE
   pg_dump trading_bot > backup_$(date +%Y%m%d).sql
   ```

4. **НЕ используй хардкод значения**
   ```sql
   -- Плохо ❌
   INSERT INTO config VALUES (1, 'localhost');
   
   -- Хорошо ✅
   INSERT INTO config (id, value) 
   VALUES (1, 'localhost')
   ON CONFLICT (id) DO NOTHING;
   ```

## 🔄 Откат миграций (Rollback)

Автоматический откат **не поддерживается**. Для отката:

### Вариант 1: Новая миграция с обратными изменениями

```sql
-- Миграция 004: Rollback add_user_settings
-- Дата: 2026-01-06

DROP TABLE IF EXISTS user_settings;
```

### Вариант 2: Ручной SQL

```sql
-- Откатить изменения вручную
DROP TABLE IF EXISTS user_settings;

-- Удалить запись из миграций (ОСТОРОЖНО!)
DELETE FROM schema_migrations WHERE version = '002';
```

### Вариант 3: Восстановление из backup

```bash
# Восстановить из backup
psql trading_bot < backup_20260104.sql
```

## 📊 Примеры миграций

### Добавление колонки
```sql
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS notes TEXT;
```

### Создание индекса
```sql
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp 
ON trades(symbol, timestamp DESC);
```

### Изменение типа колонки
```sql
-- Безопасное изменение через новую колонку
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS price_new NUMERIC(16, 8);

UPDATE trades SET price_new = price::NUMERIC(16, 8);

ALTER TABLE trades DROP COLUMN IF EXISTS price;
ALTER TABLE trades RENAME COLUMN price_new TO price;
```

### Добавление constraint
```sql
ALTER TABLE trades 
ADD CONSTRAINT IF NOT EXISTS chk_quantity_positive 
CHECK (quantity > 0);
```

## 🐛 Troubleshooting

### Проблема: "relation already exists"
**Решение:** Используй `IF NOT EXISTS` в миграции

### Проблема: Миграция не применяется в n8n
**Решение:** 
1. Проверь подключение к PostgreSQL
2. Проверь credential ID в workflow
3. Проверь права доступа БД

### Проблема: Ошибка при применении
**Решение:**
1. Проверь синтаксис SQL
2. Проверь зависимости (таблицы/колонки существуют?)
3. Проверь логи PostgreSQL

### Проблема: Нужно применить миграцию повторно
**Решение:**
```sql
-- 1. Удалить запись (ОСТОРОЖНО!)
DELETE FROM schema_migrations WHERE version = '001';

-- 2. Применить миграцию снова через workflow или скрипт
```

## 📚 Дополнительные ресурсы

- [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)
- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [n8n PostgreSQL Node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.postgres/)
