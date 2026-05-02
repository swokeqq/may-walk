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

Приложение локально запускается через Docker Compose.

1. Подготовить окружение:

```bash
cp .env.example .env
```

Для локальной разработки с доступной API документацией следует заменить `DEBUG=false` на `DEBUG=true` в `.env`.

Для локальной разработки с использованием HTTP следует заменить `AUTH_COOKIE_SECURE=true` на `AUTH_COOKIE_SECURE=false` в `.env`.

2. Поднять приложение:

```bash
docker compose up -d --build
```

3. Применить миграции:

```bash
docker compose exec backend uv run alembic upgrade head
```

4. Создать администратора:

```bash
docker compose exec backend uv run python -m may_walk.cli create-admin
```

5. Установить подготовленную карту Екатеринбурга и его окрестностей:

```bash
docker compose exec backend sh -lc 'mkdir -p /tmp/may_walk && wget -O /tmp/may_walk/yekaterinburg.geojsonseq "https://github.com/swokeqq/may-walk/releases/download/osm-reference-yekaterinburg-02-05-2026/yekaterinburg.geojsonseq" && uv run python -m may_walk.cli import-reference-segments --file /tmp/may_walk/yekaterinburg.geojsonseq --replace'
```

## Импорт Любого Региона

Backend принимает подготовленный `GeoJSON` или `GeoJSONSeq` с линейными объектами и OSM-тегами в `properties`. Подходящие теги: `highway`, `railway`, `surface`, `tracktype`, `foot` и `access`.

Импортируйте выгрузку региона в контейнер:

```bash
docker compose exec backend uv run python -m may_walk.cli import-reference-segments --file /tmp/may_walk/region.geojsonseq --replace
```

`--replace` полностью заменяет текущий слой `reference_segment` в одной транзакции. Без `--replace` импорт разрешен только в пустую таблицу.

## Проверка

Линт:

```bash
uv run ruff check .
```

Проверка форматирования:

```bash
uv run ruff format --check .
```

Тесты:

```bash
uv run pytest
```
