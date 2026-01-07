#!/bin/bash
# Скрипт автоматического применения миграций базы данных

set -e  # Останавливаться при ошибках

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Параметры подключения к БД (можно переопределить через env переменные)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-trading_bot}"
DB_USER="${DB_USER:-postgres}"

MIGRATIONS_DIR="$(dirname "$0")/migrations"

echo -e "${GREEN}🔄 Database Migration Tool${NC}"
echo "================================"
echo "Host: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "================================"
echo ""

# Функция для выполнения SQL запроса
run_sql() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$1"
}

# Функция для выполнения SQL файла
run_sql_file() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$1"
}

# Проверка наличия таблицы миграций
echo -e "${YELLOW}Проверка таблицы schema_migrations...${NC}"
TABLE_EXISTS=$(run_sql "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schema_migrations');" | xargs)

if [ "$TABLE_EXISTS" != "t" ]; then
    echo -e "${YELLOW}Таблица schema_migrations не найдена. Создаём...${NC}"
    run_sql_file "$MIGRATIONS_DIR/000_init_schema_migrations.sql"
    echo -e "${GREEN}✓ Таблица schema_migrations создана${NC}"
    echo ""
fi

# Получить список применённых миграций
echo -e "${YELLOW}Получение списка применённых миграций...${NC}"
APPLIED_MIGRATIONS=$(run_sql "SELECT version FROM schema_migrations ORDER BY version;" | xargs)
echo "Применены: ${APPLIED_MIGRATIONS:-нет}"
echo ""

# Найти все файлы миграций и отсортировать
MIGRATION_FILES=$(find "$MIGRATIONS_DIR" -name "*.sql" -type f | sort)

APPLIED_COUNT=0
SKIPPED_COUNT=0

# Применить каждую миграцию
for MIGRATION_FILE in $MIGRATION_FILES; do
    FILENAME=$(basename "$MIGRATION_FILE")
    
    # Пропустить файл 000_init_schema_migrations.sql (уже применён)
    if [[ "$FILENAME" == "000_init_schema_migrations.sql" ]]; then
        continue
    fi
    
    # Извлечь версию из имени файла
    VERSION=$(echo "$FILENAME" | grep -oE '^[0-9]+')
    NAME=$(echo "$FILENAME" | sed -E 's/^[0-9]+_//' | sed 's/.sql$//')
    
    # Проверить, применена ли миграция
    IS_APPLIED=$(echo "$APPLIED_MIGRATIONS" | grep -w "$VERSION" || echo "")
    
    if [ -n "$IS_APPLIED" ]; then
        echo -e "${GREEN}✓${NC} Migration $VERSION: $NAME (уже применена)"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        continue
    fi
    
    echo -e "${YELLOW}▶${NC} Применяю миграцию $VERSION: $NAME"
    
    # Применить миграцию
    if run_sql_file "$MIGRATION_FILE"; then
        # Зарегистрировать миграцию
        run_sql "INSERT INTO schema_migrations (version, name) VALUES ('$VERSION', '$NAME');"
        echo -e "${GREEN}✓${NC} Migration $VERSION: $NAME (применена успешно)"
        APPLIED_COUNT=$((APPLIED_COUNT + 1))
    else
        echo -e "${RED}✗${NC} Ошибка при применении миграции $VERSION: $NAME"
        exit 1
    fi
    echo ""
done

echo "================================"
echo -e "${GREEN}Применено миграций: $APPLIED_COUNT${NC}"
echo -e "${YELLOW}Пропущено (уже применены): $SKIPPED_COUNT${NC}"
echo ""
echo -e "${GREEN}✓ Все миграции применены успешно!${NC}"
