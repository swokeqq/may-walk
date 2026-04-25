"""Тесты endpoint'ов аутентификации."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from may_walk.api.dependencies import AUTH_COOKIE_NAME
from may_walk.core.passwords import hash_password
from may_walk.db.session import SessionLocal
from may_walk.models.admin_user import AdminUser
from may_walk.models.auth_session import AuthSession


@pytest.fixture(autouse=True)
def clean_auth_tables() -> None:
    """Очистить auth-таблицы до и после теста."""
    _delete_auth_rows()
    yield
    _delete_auth_rows()


def test_login_without_admin_returns_unauthenticated(client: TestClient) -> None:
    """Проверить login без созданного администратора."""
    response = client.post('/api/auth/login', json={'password': 'secret'})

    assert response.status_code == 401
    assert response.json() == {'authenticated': False}


def test_login_with_wrong_password_returns_unauthenticated(
    client: TestClient,
) -> None:
    """Проверить login с неверным паролем."""
    _create_admin('correct-password')

    response = client.post('/api/auth/login', json={'password': 'wrong-password'})

    assert response.status_code == 401
    assert response.json() == {'authenticated': False}
    assert _auth_session_count() == 0


def test_login_creates_session_and_sets_cookie(client: TestClient) -> None:
    """Проверить успешный login."""
    _create_admin('secret-password')

    response = client.post('/api/auth/login', json={'password': 'secret-password'})

    assert response.status_code == 200
    assert response.json() == {'authenticated': True}
    session_id = UUID(response.cookies[AUTH_COOKIE_NAME])

    with SessionLocal() as session:
        auth_session = session.get(AuthSession, session_id)
        assert auth_session is not None
        assert auth_session.revoked_at is None
        assert auth_session.expires_at > datetime.now(UTC)


def test_status_without_cookie_returns_unauthenticated(client: TestClient) -> None:
    """Проверить status без cookie."""
    response = client.get('/api/auth/status')

    assert response.status_code == 401
    assert response.json() == {'authenticated': False}


def test_status_with_valid_session_returns_authenticated(client: TestClient) -> None:
    """Проверить status с валидной сессией."""
    _create_admin('secret-password')
    login_response = client.post(
        '/api/auth/login',
        json={'password': 'secret-password'},
    )

    response = client.get('/api/auth/status')

    assert login_response.status_code == 200
    assert response.status_code == 200
    assert response.json() == {'authenticated': True}


def test_status_with_revoked_session_returns_unauthenticated(
    client: TestClient,
) -> None:
    """Проверить status с отозванной сессией."""
    session_id = _create_auth_session(revoked_at=datetime.now(UTC))
    client.cookies.set(AUTH_COOKIE_NAME, str(session_id))

    response = client.get('/api/auth/status')

    assert response.status_code == 401
    assert response.json() == {'authenticated': False}


def test_status_with_expired_session_returns_unauthenticated(
    client: TestClient,
) -> None:
    """Проверить status с истекшей сессией."""
    session_id = _create_auth_session(
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    client.cookies.set(AUTH_COOKIE_NAME, str(session_id))

    response = client.get('/api/auth/status')

    assert response.status_code == 401
    assert response.json() == {'authenticated': False}


def test_logout_revokes_session_and_clears_cookie(client: TestClient) -> None:
    """Проверить logout текущей сессии."""
    _create_admin('secret-password')
    login_response = client.post(
        '/api/auth/login',
        json={'password': 'secret-password'},
    )
    session_id = UUID(login_response.cookies[AUTH_COOKIE_NAME])

    response = client.post('/api/auth/logout')

    assert response.status_code == 204
    assert AUTH_COOKIE_NAME not in client.cookies
    with SessionLocal() as session:
        auth_session = session.get(AuthSession, session_id)
        assert auth_session is not None
        assert auth_session.revoked_at is not None


def test_auth_openapi_documents_unauthenticated_responses(
    client: TestClient,
) -> None:
    """Проверить документацию 401-ответов auth endpoint'ов."""
    response = client.get('/openapi.json')

    assert response.status_code == 200
    paths = response.json()['paths']
    for method, path in (
        ('post', '/api/auth/login'),
        ('get', '/api/auth/status'),
    ):
        unauthenticated_response = paths[path][method]['responses']['401']
        assert unauthenticated_response['description'] == 'Аутентификация не пройдена.'
        assert unauthenticated_response['content']['application/json']['schema'] == {
            '$ref': '#/components/schemas/AuthStatusResponse',
        }
        assert unauthenticated_response['content']['application/json']['example'] == {
            'authenticated': False,
        }

    assert '401' not in paths['/api/auth/logout']['post']['responses']


def _create_admin(password: str) -> UUID:
    """Создать администратора для теста."""
    with SessionLocal() as session:
        admin = AdminUser(password_hash=hash_password(password))
        session.add(admin)
        session.commit()
        return admin.id


def _create_auth_session(
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> UUID:
    """Создать auth-сессию для теста."""
    admin_id = _create_admin('secret-password')
    with SessionLocal() as session:
        auth_session = AuthSession(
            user_id=admin_id,
            expires_at=expires_at or datetime.now(UTC) + timedelta(hours=1),
            revoked_at=revoked_at,
        )
        session.add(auth_session)
        session.commit()
        return auth_session.id


def _auth_session_count() -> int:
    """Вернуть количество auth-сессий."""
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(AuthSession)) or 0


def _delete_auth_rows() -> None:
    """Удалить auth-данные теста."""
    with SessionLocal() as session:
        session.execute(delete(AuthSession))
        session.execute(delete(AdminUser))
        session.commit()
