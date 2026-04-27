"""Общие фикстуры и helpers для route API-тестов."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from may_walk.core.passwords import hash_password
from may_walk.db.session import SessionLocal
from may_walk.models.admin_user import AdminUser
from may_walk.models.auth_session import AuthSession
from may_walk.models.route import Route


@pytest.fixture(autouse=True)
def clean_route_tables() -> None:
    """Очистить route и auth-данные до и после теста."""
    delete_rows()
    yield
    delete_rows()


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """Вернуть клиента с валидной auth-сессией."""
    login(client)
    return client


@pytest.fixture
def line_string_geometry() -> dict[str, object]:
    """Вернуть тестовую LineString-геометрию."""
    return {
        'type': 'LineString',
        'coordinates': [[60.6, 56.83], [60.61, 56.834]],
    }


@pytest.fixture
def route_id(
    authenticated_client: TestClient,
    line_string_geometry: dict[str, object],
) -> str:
    """Создать маршрут через API и вернуть его id."""
    return create_route(authenticated_client, line_string_geometry)


def create_route(client: TestClient, geometry: dict[str, object]) -> str:
    """Создать маршрут через API и вернуть его id."""
    response = client.post(
        '/api/routes',
        json={'name': 'Route for export', 'geometry': geometry},
    )
    assert response.status_code == 201
    return response.json()['id']


def login(client: TestClient) -> None:
    """Создать администратора и выполнить login."""
    with SessionLocal() as session:
        session.add(AdminUser(password_hash=hash_password('secret-password')))
        session.commit()

    response = client.post('/api/auth/login', json={'password': 'secret-password'})
    assert response.status_code == 200


def delete_rows() -> None:
    """Удалить данные теста."""
    with SessionLocal() as session:
        session.execute(delete(AuthSession))
        session.execute(delete(AdminUser))
        session.execute(delete(Route))
        session.commit()
