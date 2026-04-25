# May Walk Backend

Бекенд для веб приложения May Walk. API построен на FastAPI, данные хранятся в PostgreSQL/PostGIS.

## API Документация

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

OpenAPI схема считается основным контрактом API. Этот документ лишь дополняет ее инструкцией запуска.

## Переменные Окружения

Все переменные окружения перечислены в `.env.example`.

- `POSTGRES_DB` - имя базы данных, которую создает контейнер PostgreSQL/PostGIS.
- `POSTGRES_USER` - пользователь PostgreSQL для Docker Compose.
- `POSTGRES_PASSWORD` - пароль пользователя PostgreSQL для Docker Compose.
- `DATABASE_URL` - строка подключения SQLAlchemy к PostgreSQL/PostGIS.
- `DEBUG` - режим отладки приложения.
- `AUTH_COOKIE_SECURE` - отправлять auth cookie только по HTTPS.
- `AUTH_COOKIE_SAMESITE` - значение `SameSite` для auth cookie.
- `AUTH_SESSION_TTL_HOURS` - срок жизни сессии в часах.

## Локальный Запуск

Приложение локально запускается через Docker Compose. Команды выполняются из корня репозитория.

1. Подготовить окружение:

```bash
cp backend/.env.example backend/.env
```

Для локальной разработки через HTTP в `backend/.env` можно заменить `AUTH_COOKIE_SECURE=true` на `AUTH_COOKIE_SECURE=false`.

2. Поднять приложение:

```bash
docker compose -f backend/compose.yml up -d --build
```

3. Применить миграции:

```bash
docker compose -f backend/compose.yml exec backend uv run alembic upgrade head
```

4. Создать администратора:

```bash
docker compose -f backend/compose.yml exec backend uv run python -m may_walk.cli create-admin
```

## Проверка

Команды проверки выполняются из директории `backend/`.

Линт:

```bash
uv run ruff check .
```

Проверка форматирования:

```bash
uv run ruff format --check .
```

Тесты с БД из Docker Compose:

```bash
DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/may_walk' uv run pytest
```
