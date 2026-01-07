# Quick Start: Database Migrations

## 🚀 Первое применение миграций

### Вариант 1: N8N (Визуальный)

```bash
# 1. Импортировать workflow в n8n
# Файл: n8n/workflows/db-migrate.json

# 2. В n8n UI:
#    - Открыть workflow "DB Migrations"
#    - Нажать "Execute Workflow"
#    - Проверить Summary
```

### Вариант 2: Bash скрипт

```bash
# 1. Перейти в папку проекта
cd /Users/gabby/git/TradingBot

# 2. Установить env переменные
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=trading_bot
export DB_USER=postgres
export DB_PASSWORD=your_password

# 3. Запустить скрипт
./db/apply_migrations.sh
```

### Вариант 3: Вручную (psql)

```bash
# 1. Создать таблицу миграций
psql -h localhost -U postgres -d trading_bot \
  -f db/migrations/000_init_schema_migrations.sql

# 2. Применить миграцию 001
psql -h localhost -U postgres -d trading_bot \
  -f db/migrations/001_add_ema_columns.sql

# 3. Зарегистрировать
psql -h localhost -U postgres -d trading_bot -c "
INSERT INTO schema_migrations (version, name) 
VALUES ('001', 'add_ema_columns')
ON CONFLICT (version) DO NOTHING;"
```

## ➕ Добавление новой миграции

### Для N8N:

1. Создать файл `db/migrations/002_your_name.sql`
2. Открыть workflow "DB Migrations"
3. Редактировать ноду "Check Pending Migrations"
4. Добавить в массив `migrations`:

```javascript
{
  version: '002',
  name: 'your_name',
  description: 'Описание изменений',
  sql: `
    ALTER TABLE mytable ADD COLUMN IF NOT EXISTS mycolumn VARCHAR(50);
  `
}
```

5. Сохранить и запустить workflow

### Для Bash:

1. Создать файл `db/migrations/002_your_name.sql`
2. Запустить `./db/apply_migrations.sh`
3. Готово! Скрипт автоматически найдет новую миграцию

## ✅ Проверка статуса

```sql
-- Все применённые миграции
SELECT * FROM schema_migrations ORDER BY version;

-- Текущая версия БД
SELECT MAX(version) FROM schema_migrations;
```

## 📋 Текущие миграции

| Version | Name | Description |
|---------|------|-------------|
| 000 | init_schema_migrations | Создание системной таблицы |
| 001 | add_ema_columns | EMA 8, 9, 13, 21, 34, 50, 100, 200 |

## 📚 Полная документация

- [db/MIGRATIONS.md](MIGRATIONS.md) - Подробное руководство
- [db/migrations/README.md](migrations/README.md) - О папке migrations
