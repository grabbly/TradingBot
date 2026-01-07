# Database Migrations

Эта папка содержит миграции базы данных для Trading Bot.

## Структура

Каждая миграция имеет формат: `NNN_description.sql`

- `NNN` - трёхзначный номер версии (000, 001, 002, ...)
- `description` - краткое описание изменений
- `.sql` - SQL скрипт миграции

## Список миграций

| Версия | Файл | Описание |
|--------|------|----------|
| 000 | `000_init_schema_migrations.sql` | Создание таблицы schema_migrations |
| 001 | `001_add_ema_columns.sql` | Добавление колонок EMA 8, 9, 13, 21, 34, 50, 100, 200 |

## Применение миграций

### Вариант 1: Через n8n workflow

1. Импортировать workflow: `n8n/workflows/db-migrate.json`
2. Запустить workflow вручную
3. Workflow автоматически применит все непримененные миграции

### Вариант 2: Вручную через psql

```bash
# 1. Создать таблицу миграций (если ещё не создана)
psql -h localhost -U your_user -d trading_bot -f db/migrations/000_init_schema_migrations.sql

# 2. Применить конкретную миграцию
psql -h localhost -U your_user -d trading_bot -f db/migrations/001_add_ema_columns.sql

# 3. Зарегистрировать миграцию
psql -h localhost -U your_user -d trading_bot -c "
INSERT INTO schema_migrations (version, name) 
VALUES ('001', 'add_ema_columns')
ON CONFLICT (version) DO NOTHING;
"
```

### Вариант 3: Применить все миграции скриптом

```bash
# Запустить скрипт автоматического применения
./db/apply_migrations.sh
```

## Создание новой миграции

1. Определить следующий номер версии (например, 002)
2. Создать файл `db/migrations/002_your_description.sql`
3. Написать SQL код миграции:
   ```sql
   -- Миграция 002: Ваше описание
   -- Дата: YYYY-MM-DD
   -- Описание: Подробное описание изменений
   
   -- Ваш SQL код здесь
   ALTER TABLE ...
   ```
4. Применить миграцию через n8n workflow или вручную

## Правила

1. **Никогда не изменяйте применённые миграции** - создавайте новую миграцию для исправлений
2. **Используйте IF NOT EXISTS / IF EXISTS** для идемпотентности
3. **Добавляйте комментарии** с датой и описанием
4. **Тестируйте на dev окружении** перед применением на prod
5. **Версии всегда идут по порядку** - 000, 001, 002, ...

## Проверка статуса миграций

```sql
-- Посмотреть все применённые миграции
SELECT version, name, applied_at 
FROM schema_migrations 
ORDER BY version;

-- Узнать последнюю версию
SELECT MAX(version) as current_version 
FROM schema_migrations;
```

## Откат миграций

Откат не поддерживается автоматически. Для отката:

1. Создайте новую миграцию с обратными изменениями
2. Или выполните ручные SQL команды для отмены изменений
3. Зарегистрируйте rollback как новую миграцию

## Troubleshooting

**Проблема**: Миграция не применяется в n8n workflow  
**Решение**: Проверьте права доступа к папке `db/migrations/` и подключение к PostgreSQL

**Проблема**: Ошибка "relation already exists"  
**Решение**: Используйте `IF NOT EXISTS` / `IF EXISTS` в миграциях

**Проблема**: Нужно применить миграцию повторно  
**Решение**: Удалите запись из `schema_migrations` и примените снова (осторожно!)
