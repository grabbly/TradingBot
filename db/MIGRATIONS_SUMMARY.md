# Database Migrations System - Summary

## ✅ Что реализовано

### 1. Структура папок
```
db/
├── migrations/                           # ✅ Папка с миграциями
│   ├── 000_init_schema_migrations.sql   # ✅ Системная таблица
│   ├── 001_add_ema_columns.sql          # ✅ EMA колонки
│   └── README.md                         # ✅ Документация папки
├── apply_migrations.sh                   # ✅ Bash скрипт
├── MIGRATIONS.md                         # ✅ Полное руководство
├── QUICKSTART_MIGRATIONS.md              # ✅ Быстрый старт
└── migrate_add_ema_columns.sql           # ⚠️ Deprecated (оставлен для обратной совместимости)
```

### 2. N8N Workflow
- **Файл**: `n8n/workflows/db-migrate.json`
- **Функции**:
  - ✅ Создание таблицы schema_migrations
  - ✅ Проверка применённых миграций
  - ✅ Применение новых миграций
  - ✅ Регистрация в БД
  - ✅ Summary результатов

### 3. Bash скрипт
- **Файл**: `db/apply_migrations.sh`
- **Функции**:
  - ✅ Автоматическое обнаружение файлов миграций
  - ✅ Проверка применённых версий
  - ✅ Последовательное применение
  - ✅ Цветной вывод
  - ✅ Обработка ошибок

### 4. Документация
- **db/MIGRATIONS.md** - Полное руководство (5000+ слов)
- **db/QUICKSTART_MIGRATIONS.md** - Быстрый старт
- **db/migrations/README.md** - О папке migrations
- **README.md** - Обновлен с информацией о миграциях

## 🎯 Как использовать

### Первое применение

**Вариант 1: N8N (рекомендуется)**
1. Импортировать `n8n/workflows/db-migrate.json`
2. Запустить workflow
3. Проверить Summary

**Вариант 2: Bash**
```bash
export DB_HOST=localhost
export DB_PASSWORD=your_password
./db/apply_migrations.sh
```

### Добавление новой миграции

**Для N8N:**
1. Создать `db/migrations/002_name.sql`
2. Добавить в workflow ноду "Check Pending Migrations"
3. Запустить workflow

**Для Bash:**
1. Создать `db/migrations/002_name.sql`
2. Запустить `./db/apply_migrations.sh`

## 📋 Текущие миграции

| Version | File | Status | Description |
|---------|------|--------|-------------|
| 000 | 000_init_schema_migrations.sql | ✅ Ready | Таблица для отслеживания миграций |
| 001 | 001_add_ema_columns.sql | ✅ Ready | EMA 8, 9, 13, 21, 34, 50, 100, 200 |

## 🔍 Таблица schema_migrations

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64)
);
```

**Колонки:**
- `version` - Номер версии (001, 002, ...)
- `name` - Имя миграции
- `applied_at` - Когда применена
- `checksum` - MD5 хэш (резерв для будущих проверок)

## 🔄 Workflow миграций

```
Manual Trigger
    ↓
Init Migrations Table (CREATE TABLE IF NOT EXISTS)
    ↓
Get Applied Migrations (SELECT version FROM schema_migrations)
    ↓
Check Pending Migrations (JS: фильтрация непримененных)
    ↓
Has Pending? (IF node)
    ├─ YES → Apply Migration (SQL)
    │         ↓
    │     Register Migration (INSERT INTO schema_migrations)
    │         ↓
    │     Summary (JS: отчёт)
    │
    └─ NO → Already Up to Date
```

## ✅ Принципы безопасности

1. **Идемпотентность**: `IF NOT EXISTS`, `IF EXISTS`
2. **Версионирование**: Строгая нумерация
3. **Неизменяемость**: Применённые миграции не меняются
4. **Проверка**: Автоматическая проверка применённых версий
5. **Логирование**: Таблица schema_migrations хранит историю

## 📊 Примеры использования

### Проверка статуса
```sql
SELECT version, name, applied_at 
FROM schema_migrations 
ORDER BY version;
```

### Текущая версия БД
```sql
SELECT MAX(version) as current_version 
FROM schema_migrations;
```

### Добавить миграцию вручную
```bash
# 1. Создать файл
cat > db/migrations/002_add_index.sql << 'EOF'
-- Миграция 002: Добавление индекса
-- Дата: 2026-01-04

CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
ON trades(timestamp DESC);
EOF

# 2. Применить через bash
./db/apply_migrations.sh

# 3. Или через n8n (добавить в workflow)
```

## 🚀 Следующие шаги

1. **Применить миграции** на dev окружении
2. **Проверить** через `SELECT * FROM schema_migrations`
3. **Протестировать** на новой БД
4. **Применить** на prod (если есть)

## 📚 Документация

- [db/MIGRATIONS.md](MIGRATIONS.md) - Полное руководство
- [db/QUICKSTART_MIGRATIONS.md](QUICKSTART_MIGRATIONS.md) - Быстрый старт
- [db/migrations/README.md](migrations/README.md) - О структуре
- [README.md](../README.md) - Главный README проекта

## ⚡ Quick Commands

```bash
# Применить миграции
./db/apply_migrations.sh

# Проверить статус
psql -d trading_bot -c "SELECT * FROM schema_migrations ORDER BY version;"

# Создать новую миграцию
touch db/migrations/002_your_name.sql

# Сделать скрипт исполняемым (если нужно)
chmod +x db/apply_migrations.sh
```

---

**Создано**: 2026-01-04  
**Версия системы**: 1.0  
**Последняя миграция**: 001
