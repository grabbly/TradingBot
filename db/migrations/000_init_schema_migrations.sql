-- Миграция 000: Создание таблицы для отслеживания миграций
-- Дата: 2026-01-04

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64)
);

-- Индекс для быстрого поиска по версии
CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);

-- Комментарий к таблице
COMMENT ON TABLE schema_migrations IS 'Отслеживание применённых миграций базы данных';
COMMENT ON COLUMN schema_migrations.version IS 'Номер версии миграции (001, 002, и т.д.)';
COMMENT ON COLUMN schema_migrations.name IS 'Описательное имя миграции';
COMMENT ON COLUMN schema_migrations.applied_at IS 'Дата и время применения миграции';
COMMENT ON COLUMN schema_migrations.checksum IS 'MD5 хэш содержимого миграции для проверки целостности';
