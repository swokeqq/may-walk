"""Тесты для healthcheck endpoint."""

from fastapi.testclient import TestClient


def test_healthcheck_returns_ok(client: TestClient) -> None:
    """Проверить, что healthcheck возвращает успешный ответ."""
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_healthcheck_openapi_documents_response(client: TestClient) -> None:
    """Проверить документацию ответа healthcheck."""
    response = client.get('/openapi.json')

    assert response.status_code == 200
    health_response = response.json()['paths']['/health']['get']['responses']['200']
    assert health_response['content']['application/json']['schema'] == {
        '$ref': '#/components/schemas/HealthResponse',
    }
