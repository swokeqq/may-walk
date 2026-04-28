"""Точечные contract-тесты OpenAPI."""

import pytest
from fastapi.testclient import TestClient


def test_healthcheck_openapi_documents_response(client: TestClient) -> None:
    """Проверить документацию ответа healthcheck."""
    health_response = _operation(client, '/health', 'get')['responses']['200']

    assert health_response['content']['application/json']['schema'] == {
        '$ref': '#/components/schemas/HealthResponse',
    }


def test_auth_openapi_documents_unauthenticated_responses(
    client: TestClient,
) -> None:
    """Проверить документацию 401-ответов auth endpoint'ов."""
    paths = _openapi(client)['paths']
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


def test_route_export_openapi_documents_file_response(client: TestClient) -> None:
    """Проверить OpenAPI-документацию файлового ответа export endpoint'а."""
    operation = _operation(client, '/api/routes/{route_id}/export', 'get')
    responses = operation['responses']
    success_response = responses['200']

    assert '200' in responses
    assert set(success_response['content']) >= {
        'application/geo+json',
        'application/gpx+xml',
        'application/vnd.google-earth.kml+xml',
    }
    assert 'Content-Disposition' in success_response['headers']
    assert '400' in responses
    assert '404' in responses


def test_route_import_openapi_documents_multipart_request(
    client: TestClient,
) -> None:
    """Проверить OpenAPI-документацию multipart import endpoint'а."""
    openapi = _openapi(client)
    operation = openapi['paths']['/api/routes/import']['post']
    multipart_schema = operation['requestBody']['content']['multipart/form-data'][
        'schema'
    ]
    body_schema = _resolve_ref(openapi, multipart_schema)
    responses = operation['responses']

    assert set(body_schema['properties']) >= {'file', 'name', 'snap'}
    assert 'file' in body_schema['required']
    assert responses['400']['content']['application/json']['example'] == {
        'detail': 'Route import with snap is not supported yet'
    }
    assert '422' in responses


@pytest.mark.parametrize(
    ('path', 'method'),
    [
        ('/api/routes', 'get'),
        ('/api/routes', 'post'),
        ('/api/routes/{route_id}', 'get'),
        ('/api/routes/{route_id}', 'patch'),
        ('/api/routes/{route_id}', 'delete'),
        ('/api/routes/import', 'post'),
        ('/api/routes/{route_id}/export', 'get'),
    ],
)
def test_protected_routes_openapi_document_unauthorized_response(
    client: TestClient,
    path: str,
    method: str,
) -> None:
    """Проверить описание 401 для защищенных route endpoint'ов."""
    operation = _operation(client, path, method)

    assert operation['responses']['401'] == {
        'description': 'Необходима cookie-аутентификация mw_session.'
    }


def _operation(client: TestClient, path: str, method: str) -> dict[str, object]:
    """Вернуть OpenAPI operation object."""
    return _openapi(client)['paths'][path][method]


def _openapi(client: TestClient) -> dict[str, object]:
    """Вернуть OpenAPI-схему приложения."""
    response = client.get('/openapi.json')
    assert response.status_code == 200
    return response.json()


def _resolve_ref(
    openapi: dict[str, object],
    schema: dict[str, object],
) -> dict[str, object]:
    """Разыменовать локальный $ref на schema object."""
    ref = schema.get('$ref')
    if not isinstance(ref, str):
        return schema

    value: object = openapi
    for segment in ref.removeprefix('#/').split('/'):
        assert isinstance(value, dict)
        value = value[segment]

    assert isinstance(value, dict)
    return value
