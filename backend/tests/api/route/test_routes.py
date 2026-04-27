"""Тесты CRUD endpoint'ов маршрутов."""

from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.route.conftest import line_string_geometry


def test_routes_require_auth(client: TestClient) -> None:
    """Проверить защиту CRUD endpoint'ов маршрутов."""
    route_id = uuid4()

    responses = [
        client.get('/api/routes'),
        client.post('/api/routes', json={'name': 'Route'}),
        client.get(f'/api/routes/{route_id}'),
        client.patch(f'/api/routes/{route_id}', json={'name': 'Route'}),
        client.delete(f'/api/routes/{route_id}'),
    ]

    assert {response.status_code for response in responses} == {401}


def test_route_crud_without_total_length(authenticated_client: TestClient) -> None:
    """Проверить CRUD маршрута без total_length_m в ответах."""
    create_response = authenticated_client.post(
        '/api/routes',
        json={
            'name': 'Route 1',
            'geometry': line_string_geometry(),
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    route_id = created['id']
    assert created['name'] == 'Route 1'
    assert created['geometry']['type'] == 'MultiLineString'
    assert 'total_length_m' not in created

    list_response = authenticated_client.get('/api/routes')

    assert list_response.status_code == 200
    listed = list_response.json()['items'][0]
    assert listed['id'] == route_id
    assert listed['name'] == 'Route 1'
    assert 'geometry' not in listed
    assert 'total_length_m' not in listed

    get_response = authenticated_client.get(f'/api/routes/{route_id}')

    assert get_response.status_code == 200
    assert get_response.json()['geometry']['type'] == 'MultiLineString'
    assert 'total_length_m' not in get_response.json()

    patch_response = authenticated_client.patch(
        f'/api/routes/{route_id}',
        json={'name': 'Route 1 updated'},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()['name'] == 'Route 1 updated'
    assert 'total_length_m' not in patch_response.json()

    delete_response = authenticated_client.delete(f'/api/routes/{route_id}')

    assert delete_response.status_code == 204
    assert authenticated_client.get(f'/api/routes/{route_id}').status_code == 404
