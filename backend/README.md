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
- `OSRM_URL` - строка подключения к OSRM.
- `OSRM_PBF_URL` - URL единого PBF-файла для OSRM и `reference_segment`.
- `OSRM_TIMEOUT_S` - timeout запросов к OSRM в секундах.
- `OSRM_RADIUS_M` - радиус поиска OSRM `/match` в метрах.
- `OSRM_MAX_MATCHING_SIZE` - максимальное число точек в одном OSRM `/match`.

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

При первом запуске Docker Compose скачивает PBF из `OSRM_PBF_URL` в named volume,
строит OSRM-граф, экспортирует `reference.geojsonseq`, применяет миграции и
импортирует `reference_segment`. При последующих запусках слой опорных сегментов
переимпортируется только если hash `reference.geojsonseq` изменился.

3. Создать администратора:

```bash
docker compose exec backend uv run python -m may_walk.cli create-admin
```

## Обновление OSM PBF

Замените `OSRM_PBF_URL` в `.env` и пересоздайте init-сервисы:

```bash
docker compose up -d --build --force-recreate
```

Смена URL очищает производные файлы в volume: `map.osrm*` и
`reference.geojsonseq`. После этого OSRM-граф и `reference_segment` строятся из
нового PBF.

## Обновление ппорных сегментов

Основной сценарий не требует ручного GeoJSONSeq: `reference-init` создает
`reference.geojsonseq` из PBF через `osmium export`, а backend импортирует его
при старте. CLI-команда остается для диагностики и ручного восстановления:

```bash
docker compose exec backend uv run python -m may_walk.cli import-reference-segments --file /data/reference.geojsonseq --replace-if-changed
```

Backend принимает подготовленный `GeoJSON` или `GeoJSONSeq` с линейными
объектами и OSM-тегами в `properties`. Подходящие теги: `highway`, `railway`,
`surface`, `tracktype`, `foot` и `access`.

Для принудительной замены слоя используйте:

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
