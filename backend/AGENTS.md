# Backend Notes

- Работай из `backend/`. CI запускает backend-команды с `working-directory: backend`, а `pytest` использует `pythonpath = ["src"]` из `backend/pyproject.toml`.
- Backend собран как `src`-пакет `may_walk`. ASGI entrypoint: `may_walk.main:app`.
- Комментарии, docstring'и и локальная документация в backend пишутся на русском.

## Команды

- Установить зависимости: `uv sync --dev --frozen`
- Линт: `uv run ruff check .`
- Проверка форматирования: `uv run ruff format --check .`
- Все тесты: `uv run pytest`
- Один тест: `uv run pytest tests/api/test_health.py`
- Миграции: `uv run alembic upgrade head`
- Локальный запуск API: `uv run uvicorn may_walk.main:app --host 0.0.0.0 --port 8000`

## Настройки И БД

- Настройки создаются сразу при импорте в `src/may_walk/core/settings.py` как глобальный объект `settings`.
- У `DATABASE_URL` нет значения по умолчанию. Все сценарии, которые импортируют `may_walk.db.session` или запускают Alembic, требуют заранее заданный `DATABASE_URL`.
- Локальный Docker-стек живет в `backend/compose.yml` и читает `backend/.env`. Для новой машины начинай с `backend/.env.example`.
- Из корня репозитория backend-стек поднимается так: `docker compose -f backend/compose.yml up`.

## Alembic И PostGIS

- Alembic настроен в `backend/alembic.ini`; `backend/alembic/env.py` вручную добавляет `backend/src` в `sys.path` из-за `src`-layout. Если меняешь структуру пакета, обнови и `alembic/env.py`.
- Первая миграция `backend/alembic/versions/20260424_000001_enable_postgis.py` только включает расширение `postgis`. Ее `downgrade()` не удаляет расширение, потому что в `postgis/postgis` образе от него зависят дополнительные расширения.

## Схема БД

- Для геометрий используй колонку `geometry`, не `geom`.
- `route` хранит `id`, `name`, `geometry`, `created_at`, `updated_at`. Поле `notes` не добавляй: функциональность комментариев не входит в MVP.
- `reference_segment` хранит `id`, `geometry`, `surface_class`. Поле `is_walkable` не добавляй: неподходящие сегменты должны отфильтровываться при подготовке слоя.
- `admin_user` хранит только `id`, `password_hash`, `created_at`, `updated_at`. Не добавляй `username`, `email` или `is_active` без отдельного решения.
- `auth_session` хранит `id`, `user_id`, `expires_at`, `created_at`, `revoked_at`. Поле `last_seen_at` не добавляй. `expires_at` отвечает за автоматическое истечение сессии, `revoked_at` — за logout.

## Проверка Изменений

- Для обычных backend-изменений повторяй порядок из CI: `uv sync --dev --frozen` -> `uv run ruff check .` -> `uv run ruff format --check .` -> `uv run pytest`.
- DB-зависимые проверки локально запускай только после поднятия PostGIS и `uv run alembic upgrade head`.
- Если Docker-стек поднят с проброшенным портом, локально запускай Alembic и DB-тесты с `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/may_walk`. Host `db` работает только внутри Docker-сети.
- GitHub Actions workflow: `.github/workflows/backend-ci.yml`. Job `test` поднимает `postgis/postgis:17-3.5`, задает `DATABASE_URL`, потом применяет миграции и запускает `pytest`.
