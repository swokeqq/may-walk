"""Тесты endpoint'а объединения маршрутов."""

from uuid import uuid4

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

_OSRM_URL = 'http://osrm:5000'


def test_route_merge_requires_auth(client: TestClient) -> None:
    """Проверить защиту endpoint'а объединения."""
    response = client.post('/api/routes/merge')

    assert response.status_code == 401


def test_route_merge_returns_not_found(authenticated_client: TestClient) -> None:
    """Проверить ответ для неизвестного маршрута."""
    response = authenticated_client.post(
        '/api/routes/merge',
        json={'route_ids': [str(uuid4())]},
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Route not found'


def test_route_merge_without_geometry_returns_error(
    authenticated_client: TestClient,
) -> None:
    """Проверить ответ для маршрута без геометрии."""
    create_response = authenticated_client.post('/api/routes', json={'name': 'Empty'})
    route_id = create_response.json()['id']

    response = authenticated_client.post(
        '/api/routes/merge',
        json={'route_ids': [route_id]},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == {'error': 'Route has no geometry'}


def test_route_merge_rejects_duplicate_route_ids(
    authenticated_client: TestClient,
    line_string_geometry: dict[str, object],
) -> None:
    """Проверить валидацию дублей в `route_ids`."""
    route_id = _create_route(authenticated_client, line_string_geometry)

    response = authenticated_client.post(
        '/api/routes/merge',
        json={'route_ids': [route_id, route_id]},
    )

    assert response.status_code == 422
    assert response.json()['detail'] == 'route_ids must not contain duplicates'


@respx.mock
def test_route_merge_returns_geometry_without_stats_or_length(
    authenticated_client: TestClient,
) -> None:
    """Проверить форму успешного ответа без статистики и длины."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        side_effect=[
            Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]])),
            Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]])),
        ]
    )
    first_route_id = _create_route(
        authenticated_client,
        {'type': 'LineString', 'coordinates': [[0, 0.00005], [0.001, 0.00005]]},
    )
    second_route_id = _create_route(
        authenticated_client,
        {'type': 'LineString', 'coordinates': [[0, 0.00004], [0.001, 0.00004]]},
    )

    response = authenticated_client.post(
        '/api/routes/merge',
        json={'route_ids': [first_route_id, second_route_id]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {'merged_geometry'}
    assert payload['merged_geometry']['type'] == 'MultiLineString'
    assert 'stats' not in payload
    assert 'total_m' not in payload
    assert 'total_length_m' not in payload
    assert 'similarity_score' not in payload
    assert payload['merged_geometry']['coordinates'][0][0] == pytest.approx([0, 0])


def _create_route(client: TestClient, geometry: dict[str, object]) -> str:
    """Создать маршрут через API и вернуть его id."""
    response = client.post(
        '/api/routes',
        json={'name': 'Merge route', 'geometry': geometry},
    )
    assert response.status_code == 201
    return response.json()['id']


def _osrm_ok(*lines: list[list[float]]) -> dict:
    """Сформировать успешный ответ OSRM /match с переданными линиями."""
    return {
        'code': 'Ok',
        'matchings': [
            {'geometry': {'type': 'LineString', 'coordinates': coords}}
            for coords in lines
        ],
    }
