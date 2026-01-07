# Обновление системы сбора EMA данных

## Что изменено

Добавлена поддержка расширенного набора EMA периодов: **5, 8, 9, 13, 20, 21, 34, 50, 100, 200**

## Изменённые файлы

### 1. База данных
- **db/schema.sql** - обновлена схема с новыми колонками EMA
- **db/migrate_add_ema_columns.sql** - SQL миграция для существующей БД

### 2. N8N Workflow
- **n8n/workflows/ema-logger.json** - обновлён для расчета всех EMA периодов
  - Увеличен лимит баров с 50 до 250 (для EMA200)
  - Обновлена нода "Calculate EMA" для расчета всех периодов
  - Обновлена нода "Detect Signal" для работы с новой структурой данных
  - Обновлен SQL INSERT для сохранения всех EMA значений

### 3. JavaScript библиотека
- **src/ema.js** - добавлена функция `calculateMultipleEMA()`

## Шаги по применению

### Шаг 1: Обновление базы данных

Для **существующей** базы данных выполните миграцию:

```bash
psql -h localhost -U your_user -d trading_bot -f db/migrate_add_ema_columns.sql
```

Для **новой** базы данных используйте обновленную схему:

```bash
psql -h localhost -U your_user -d trading_bot -f db/schema.sql
```

### Шаг 2: Обновление N8N Workflow

1. Откройте n8n UI
2. Импортируйте обновленный файл: `n8n/workflows/ema-logger.json`
3. Убедитесь, что credentials настроены:
   - Alpaca API (httpCustomAuth)
   - PostgreSQL Trading

### Шаг 3: Проверка

После применения изменений проверьте:

```sql
-- Проверка структуры таблицы
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ema_snapshots' 
AND column_name LIKE 'ema%'
ORDER BY column_name;

-- Проверка последних записей (должны содержать все EMA)
SELECT timestamp, symbol, close_price, 
       ema5, ema8, ema9, ema13, ema20, ema21, 
       ema34, ema50, ema100, ema200
FROM ema_snapshots 
ORDER BY timestamp DESC 
LIMIT 5;
```

## Важные изменения в коде

### Calculate EMA (n8n node)
Теперь расчитывает все периоды в цикле:
```javascript
config.periods.forEach(period => {
  if (closes.length >= period) {
    const ema = calculateEMA(closes, period);
    current[`ema${period}`] = ema[last];
    previous[`ema${period}`] = ema[prev];
  }
});
```

### SQL INSERT
Обновлён для включения всех EMA колонок:
```sql
INSERT INTO ema_snapshots (
  timestamp, symbol, close_price, 
  ema5, ema8, ema9, ema13, ema20, ema21, 
  ema34, ema50, ema100, ema200, 
  action, crossover, message
)
```

## Проверка работы

1. Запустите workflow в n8n
2. Дождитесь нескольких циклов сбора данных (каждые 3 секунды)
3. Проверьте, что данные записываются в БД со всеми EMA значениями
4. Для EMA100 и EMA200 потребуется больше времени для накопления данных (250 5-минутных баров = ~21 час торговли)

## Структура данных

### Объект `current` в workflow:
```javascript
{
  close: 145.32,
  timestamp: "2026-01-04T10:30:00Z",
  ema5: 145.21,
  ema8: 145.18,
  ema9: 145.15,
  ema13: 145.10,
  ema20: 144.98,
  ema21: 144.95,
  ema34: 144.80,
  ema50: 144.65,
  ema100: 144.20,
  ema200: 143.50
}
```

## Совместимость

- Старые записи в БД останутся с NULL в новых колонках EMA
- Workflow совместим с предыдущей версией (основная логика на EMA5/EMA20 не изменена)
- Новые данные будут содержать все EMA периоды
