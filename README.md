# AI-Recruiter System

Интеллектуальная система подбора персонала для ПЦП ЕРКЦ (г. Екатеринбург)

## Структура

### Развертывание

`deploy` - развертывание

### Telegram бот

`src/bot` - модуль Telegram бота

`src/bot/core` - основная логика бота

`src/bot/handlers` - обработчики сообщений

`src/bot/utils` - вспомогательные функции

### База данных

`src/database` - модуль логики работы с БД

`src/database/models` - модели сущностей БД

`src/database/migrations` - миграции БД

`src/database/utils` - вспомогательные функции

### GigaChat

`src/gigachat_module` - модуль логики работы с моделью GigaChat

### Тестирование

`tests` - тесты

### Общее

`requirements.txt` - зависимости Python

`alembic.ini` - конфигурация Alembic