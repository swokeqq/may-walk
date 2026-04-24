"""Тесты для healthcheck endpoint."""

from fastapi.testclient import TestClient


def test_healthcheck_returns_ok(client: TestClient) -> None:
    """Проверить, что healthcheck возвращает успешный ответ."""
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
