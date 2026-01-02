-- Выполнить от имени postgres superuser
-- psql -h ***REMOVED*** -U postgres -f db/init.sql

-- 1. Создать пользователя (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'n8n_user') THEN
        CREATE USER n8n_user WITH PASSWORD '***REMOVED***';
    END IF;
END
$$;

-- 2. Создать базу данных
CREATE DATABASE trading_bot OWNER n8n_user;

-- 3. Подключиться к новой базе и выдать права
\c trading_bot

-- Выдать права пользователю
GRANT ALL PRIVILEGES ON DATABASE trading_bot TO n8n_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO n8n_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO n8n_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO n8n_user;
