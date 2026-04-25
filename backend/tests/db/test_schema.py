"""Интеграционные тесты схемы базы данных."""

from collections.abc import Iterable

from sqlalchemy import text

from may_walk.db.session import engine


def _fetch_column_names(table_name: str) -> set[str]:
    """Получить имена колонок таблицы из information_schema."""
    query = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :table_name
        """,
    )

    with engine.connect() as connection:
        return set(connection.execute(query, {'table_name': table_name}).scalars())


def _fetch_index_names(table_name: str) -> set[str]:
    """Получить имена индексов таблицы из pg_indexes."""
    query = text(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = :table_name
        """,
    )

    with engine.connect() as connection:
        return set(connection.execute(query, {'table_name': table_name}).scalars())


def _fetch_constraint_names(table_name: str, constraint_type: str) -> set[str]:
    """Получить имена ограничений таблицы из pg_constraint."""
    query = text(
        """
        SELECT pg_constraint.conname
        FROM pg_constraint
        JOIN pg_class AS table_class ON table_class.oid = pg_constraint.conrelid
        JOIN pg_namespace AS namespace ON namespace.oid = table_class.relnamespace
        WHERE namespace.nspname = 'public'
            AND table_class.relname = :table_name
            AND pg_constraint.contype = :constraint_type
        """,
    )

    with engine.connect() as connection:
        return set(
            connection.execute(
                query,
                {'table_name': table_name, 'constraint_type': constraint_type},
            ).scalars(),
        )


def _assert_has_columns(table_name: str, expected_columns: Iterable[str]) -> None:
    """Проверить точный набор колонок таблицы."""
    assert set(expected_columns) == _fetch_column_names(table_name)


def test_tables_exist() -> None:
    """Проверить наличие таблиц маршрутов, опорной сети и auth."""
    query = text(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """,
    )

    with engine.connect() as connection:
        table_names = set(connection.execute(query).scalars())

    assert {
        'admin_user',
        'auth_session',
        'reference_segment',
        'route',
    }.issubset(table_names)


def test_route_schema() -> None:
    """Проверить колонки и spatial index маршрутов."""
    _assert_has_columns('route', {'id', 'name', 'geometry', 'created_at', 'updated_at'})
    assert 'ix_route_geometry' in _fetch_index_names('route')


def test_reference_segment_schema() -> None:
    """Проверить колонки, spatial index и CHECK покрытия опорных сегментов."""
    _assert_has_columns('reference_segment', {'id', 'geometry', 'surface_class'})
    assert 'ix_reference_segment_geometry' in _fetch_index_names('reference_segment')
    assert 'ck_reference_segment_surface_class' in _fetch_constraint_names(
        'reference_segment',
        'c',
    )


def test_admin_user_schema() -> None:
    """Проверить колонки администратора и статуса активности."""
    _assert_has_columns(
        'admin_user', {'id', 'password_hash', 'created_at', 'updated_at'}
    )
    assert 'uq_admin_user_singleton' in _fetch_index_names('admin_user')


def test_auth_session_schema() -> None:
    """Проверить колонки, индексы и внешний ключ auth-сессий."""
    _assert_has_columns(
        'auth_session',
        {'id', 'user_id', 'expires_at', 'created_at', 'revoked_at'},
    )
    assert {
        'ix_auth_session_user_id',
        'ix_auth_session_expires_at',
        'ix_auth_session_revoked_at',
    }.issubset(_fetch_index_names('auth_session'))
    assert _fetch_constraint_names('auth_session', 'f')
