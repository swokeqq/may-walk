# Backend Notes

- Работай из `backend/`. CI запускает backend-команды с `working-directory: backend`, а `pytest` использует `pythonpath = ["src"]` из `backend/pyproject.toml`.
- Backend собран как `src`-пакет `may_walk`. ASGI entrypoint: `may_walk.main:app`.
- Комментарии, docstring'и и локальная документация в backend пишутся на русском.

## Команды

- Установить зависимости: `uv sync --dev --frozen`
- Линт: `uv run ruff check .`
- Проверка форматирования: `uv run ruff format --check .`
- Все тесты: `uv run pytest`
- Все тесты локально в PowerShell с БД на localhost: `$env:DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/may_walk'; uv run pytest`
- Один тест: `uv run pytest tests/api/test_health.py`
- Один DB-зависимый тест локально в PowerShell: `$env:DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/may_walk'; uv run pytest tests/api/test_authentication.py`
- Миграции: `uv run alembic upgrade head`
- Создать первого администратора: `uv run python -m may_walk.cli create-admin`
- Импортировать подготовленную опорную карту вручную: `uv run python -m may_walk.cli import-reference-segments --file /path/to/reference.geojsonseq --replace`
- Локальный запуск API: `uv run uvicorn may_walk.main:app --host 0.0.0.0 --port 8000`

## Структура Кода

- Для новых файлов предпочитай полные имена вместо сокращений: `dependencies.py`, `authentication.py`, а не `deps.py` или `auth.py`.
- API роутеры размещай в `src/may_walk/api/routers/`; для доменных групп можно использовать подпакеты, например `src/may_walk/api/routers/route/`.
- `src/may_walk/api/router.py` должен только собирать роутеры.
- CLI живет в пакете `src/may_walk/cli/`; `python -m may_walk.cli` работает через `src/may_walk/cli/__main__.py`.
- Новые CLI-команды добавляй отдельными файлами в `src/may_walk/cli/commands/`, реализуй контракт `CliCommand` из `src/may_walk/cli/protocol.py` и регистрируй команду в `src/may_walk/cli/registry.py`. Не добавляй ветвление по именам команд в `application.py`.
- CLI-команды не должны импортировать `may_walk.db.session` на уровне модуля: DB-зависимые импорты делай внутри `run()`, чтобы `--help` работал без `DATABASE_URL`.
- Route CRUD-сервисы размещай в `src/may_walk/services/route/`, файловые операции маршрутов — в `src/may_walk/services/route_file/`, OSM-операции маршрутов — в `src/may_walk/services/route_osm/`.
- Сервис объединения маршрутов размещай в `src/may_walk/services/route_osm/merge/`; ошибки объединения держи в отдельном `errors.py` внутри этого пакета.
- Реализации route import/export форматов держи отдельными handler-классами по файлам форматов, а регистрацию форматов — в `route_file/imports/__init__.py` и `route_file/exports/__init__.py`.
- Сервисы опорных сегментов размещай в `src/may_walk/services/reference_segments/`: классификация OSM-тегов в `classification/`, разбор подготовленных GeoJSON/GeoJSONSeq файлов в `imports/`, загрузка в БД в `storage/`.

## Настройки И БД

- `src/may_walk/core/` хранит базовую инфраструктуру приложения: настройки, auth-cookie константы и хеширование паролей. Не переноси туда API dependencies, DB session или доменные сервисы.
- Настройки создаются сразу при импорте в `src/may_walk/core/settings.py` как глобальный объект `settings`.
- У `DATABASE_URL` нет значения по умолчанию. Все сценарии, которые импортируют `may_walk.db.session` или запускают Alembic, требуют заранее заданный `DATABASE_URL`.
- Локальный Docker-стек живет в `compose.yml` и читает `.env`. Для новой машины начинай с `.env.example`.
- Из директории `backend/` backend-стек поднимается так: `docker compose -f compose.yml up`.
- В `.env.example` `AUTH_COOKIE_SECURE=true`; для локальной разработки через HTTP в `.env` можно задавать `AUTH_COOKIE_SECURE=false`.

## Alembic И PostGIS

- Alembic настроен в `backend/alembic.ini`; `backend/alembic/env.py` вручную добавляет `backend/src` в `sys.path` из-за `src`-layout. Если меняешь структуру пакета, обнови и `alembic/env.py`.
- Первая миграция `backend/alembic/versions/20260424_000001_enable_postgis.py` только включает расширение `postgis`. Ее `downgrade()` не удаляет расширение, потому что в `postgis/postgis` образе от него зависят дополнительные расширения.

## Схема БД

- Для геометрий используй колонку `geometry`, не `geom`.
- `route` хранит `id`, `name`, `geometry`, `created_at`, `updated_at`. Поле `notes` не добавляй: функциональность комментариев не входит в MVP.
- `reference_segment` хранит `id`, `geometry`, `surface_class`. Поле `is_walkable` не добавляй: неподходящие сегменты должны отфильтровываться при подготовке слоя.
- `admin_user` хранит только `id`, `password_hash`, `created_at`, `updated_at`. Не добавляй `username`, `email` или `is_active` без отдельного решения.
- В `admin_user` допускается не больше одной записи; это ограничено индексом `uq_admin_user_singleton`.
- `auth_session` хранит `id`, `user_id`, `expires_at`, `created_at`, `revoked_at`. Поле `last_seen_at` не добавляй. `expires_at` отвечает за автоматическое истечение сессии, `revoked_at` — за logout.

## Опорные Сегменты

- `reference_segment` не заполняется публичным API. В Docker-сценарии `reference-init` создает `/data/reference.geojsonseq` из единого PBF, а backend при старте идемпотентно запускает CLI-команду `import-reference-segments --replace-if-changed`.
- CLI принимает подготовленный и распакованный `GeoJSON` или `GeoJSONSeq` в `EPSG:4326`. Основной локальный источник данных — PBF из `OSRM_PBF_URL`; ручной GeoJSONSeq импорт нужен только для диагностики или восстановления.
- Неподходящие для расчетной сети OSM-объекты отбрасываются до вставки в БД; поле `is_walkable` не добавляй.
- Без `--replace` импорт разрешен только в пустую таблицу `reference_segment`; `--replace` заменяет слой в текущей транзакции. `--replace-if-changed` заменяет слой только если SHA-256 файла отличается от последнего импортированного.

## Аутентификация

- Первый администратор создается только интерактивной CLI-командой `uv run python -m may_walk.cli create-admin`; пароль не читается из env.
- Auth использует серверные сессии в `auth_session` и `HttpOnly` cookie `mw_session`.
- Для неуспешной аутентификации используй `401 Unauthorized`; `403 Forbidden` пока не используется, потому что нет ролей, прав доступа или `is_active`.
- Защищенные endpoint'ы должны использовать dependency `require_auth()` из `src/may_walk/api/dependencies.py`.

## Маршруты

- CRUD endpoint'ы маршрутов живут в `src/may_walk/api/routers/route/crud.py`.
- Импорт маршрутов живет в `src/may_walk/api/routers/route_file/imports.py`, экспорт — в `src/may_walk/api/routers/route_file/exports.py`.
- Stats endpoint маршрутов живет в `src/may_walk/api/routers/route_osm/stats.py`, расчет — в `src/may_walk/services/route_osm/stats.py`.
- Snap endpoint маршрутов живет в `src/may_walk/api/routers/route_osm/snap.py`, расчет примагничивания — в `src/may_walk/services/route_osm/snap.py` через OSRM `/match`.
- Merge endpoint маршрутов живет в `src/may_walk/api/routers/route_osm/merge.py`, расчет — в `src/may_walk/services/route_osm/merge/`.
- CRUD/import ответы маршрутов не должны возвращать `total_length_m`; длина относится к `stats` endpoint'у.
- Merge endpoint ничего не сохраняет и возвращает только `merged_geometry`; не добавляй в ответ `total_length_m`, `total_m`, `stats` или `similarity_score`.
- В merge близкие или дублирующиеся участки схлопываются, а далекие компоненты остаются отдельными линиями в `MultiLineString`; не соединяй их искусственной линией.
- В stats `total_m` считается по полной длине `route.geometry`, независимо от OSM. Длины по покрытиям считаются по сегментам маршрута: сначала точное линейное совпадение с `reference_segment`, затем ближайший сегмент в пределах допуска. Несопоставленные участки попадают в `other_m`.
- Все GeoJSON-геометрии в API должны быть в `EPSG:4326`; `LineString` на входе нормализуется в `MultiLineString`.
- Импорт маршрутов поддерживает `snap=true`: геометрия примагничивается через OSRM `/match`, а участки без совпадения или при ошибке OSRM сохраняются как есть.
- Для новых форматов import/export добавляй новый handler и регистрируй его в соответствующем registry, не добавляй ветвление в endpoint'ы.

## OpenAPI Документация

- FastAPI/OpenAPI является основным контрактом API; документируй поведение, важное для клиента, в Swagger-описаниях.
- Описания полей в Pydantic-схемах держи краткими: одно предложение или несколько слов.
- Основное поведение endpoint'а описывай в docstring функции endpoint'а.
- Необычное поведение полей, query/form-параметров и ответов явно документируй в endpoint'е.
- Имена полей, query/form-параметры, значения enum, имена файлов, расширения и форматы выделяй через backticks, например `geometry`, `format`, `geojson`, `.gpx`.
- Не добавляй frontend-инструкции или очевидные предупреждения, если они не являются частью API-контракта.

## Проверка Изменений

- Для обычных backend-изменений повторяй порядок из CI: `uv sync --dev --frozen` -> `uv run ruff check .` -> `uv run ruff format --check .` -> `uv run pytest`.
- DB-зависимые проверки локально запускай только после поднятия PostGIS и `uv run alembic upgrade head`.
- Если Docker-стек поднят с проброшенным портом, локально запускай Alembic и DB-тесты с `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/may_walk`; в PowerShell задавай переменную как `$env:DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/may_walk'; <command>`. Host `db` работает только внутри Docker-сети.
- Route API-тесты лежат в `tests/api/route/`, `tests/api/route_file/` и `tests/api/route_osm/`; локально их можно запускать так: `$env:DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/may_walk'; uv run pytest tests/api/route tests/api/route_file tests/api/route_osm`.
- GitHub Actions workflow: `.github/workflows/backend-ci.yml`. Job `test` поднимает `postgis/postgis:17-3.5`, задает `DATABASE_URL`, потом применяет миграции и запускает `pytest`.
