"""Тесты endpoint'а статистики маршрутов."""

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func

from may_walk.db.session import SessionLocal
from may_walk.models.reference_segment import ReferenceSegment


def test_route_stats_requires_auth(client: TestClient) -> None:
    """Проверить защиту endpoint'а статистики."""
    response = client.get(f'/api/routes/{uuid4()}/stats')

    assert response.status_code == 401


def test_route_stats_returns_not_found(authenticated_client: TestClient) -> None:
    """Проверить ответ для неизвестного маршрута."""
    response = authenticated_client.get(f'/api/routes/{uuid4()}/stats')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Route not found'


def test_route_stats_without_geometry_returns_error(
    authenticated_client: TestClient,
) -> None:
    """Проверить ответ для маршрута без геометрии."""
    create_response = authenticated_client.post('/api/routes', json={'name': 'Empty'})
    route_id = create_response.json()['id']

    response = authenticated_client.get(f'/api/routes/{route_id}/stats')

    assert response.status_code == 400
    assert response.json()['detail'] == {'error': 'Route has no geometry'}


def test_route_stats_groups_lengths_by_surface_class(
    authenticated_client: TestClient,
) -> None:
    """Проверить группировку длин по классам покрытия."""
    _insert_reference_segments()
    create_response = authenticated_client.post(
        '/api/routes',
        json={
            'name': 'Stats route',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[0, 0], [0.001, 0], [0.002, 0]],
            },
        },
    )
    route_id = create_response.json()['id']

    response = authenticated_client.get(f'/api/routes/{route_id}/stats')

    payload = response.json()

    assert response.status_code == 200
    assert set(payload) == {
        'asphalt_m',
        'forest_path_m',
        'field_path_m',
        'rail_m',
        'other_m',
        'total_m',
    }
    assert payload['asphalt_m'] == pytest.approx(111.32, abs=1)
    assert payload['forest_path_m'] == pytest.approx(111.32, abs=1)
    assert payload['field_path_m'] == 0
    assert payload['rail_m'] == 0
    assert payload['other_m'] == 0
    assert payload['total_m'] == pytest.approx(
        payload['asphalt_m'] + payload['forest_path_m'], abs=0.01
    )


def test_route_stats_matches_nearby_reference_segments(
    authenticated_client: TestClient,
) -> None:
    """Проверить расчет для GPS-трека рядом с опорной сетью."""
    _insert_reference_segments()
    create_response = authenticated_client.post(
        '/api/routes',
        json={
            'name': 'Nearby stats route',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[0, 0.00005], [0.0009, 0.00005]],
            },
        },
    )
    route_id = create_response.json()['id']

    response = authenticated_client.get(f'/api/routes/{route_id}/stats')

    payload = response.json()

    assert response.status_code == 200
    assert payload['asphalt_m'] == pytest.approx(100.19, abs=1)
    assert payload['forest_path_m'] == 0
    assert payload['field_path_m'] == 0
    assert payload['rail_m'] == 0
    assert payload['other_m'] == 0
    assert payload['total_m'] == pytest.approx(payload['asphalt_m'], abs=0.01)


def test_route_stats_mixes_exact_nearby_and_unmatched_segments(
    authenticated_client: TestClient,
) -> None:
    """Проверить смешанный маршрут с точными, примерными и прочими участками."""
    _insert_reference_segments()
    create_response = authenticated_client.post(
        '/api/routes',
        json={
            'name': 'Mixed stats route',
            'geometry': {
                'type': 'MultiLineString',
                'coordinates': [
                    [[0, 0], [0.001, 0]],
                    [[0.001, 0.00005], [0.0019, 0.00005]],
                    [[0.02, 0.02], [0.021, 0.02]],
                ],
            },
        },
    )
    route_id = create_response.json()['id']

    response = authenticated_client.get(f'/api/routes/{route_id}/stats')

    payload = response.json()

    assert response.status_code == 200
    assert payload['asphalt_m'] == pytest.approx(111.32, abs=1)
    assert payload['forest_path_m'] == pytest.approx(100.19, abs=1)
    assert payload['field_path_m'] == 0
    assert payload['rail_m'] == 0
    assert payload['other_m'] == pytest.approx(111.32, abs=1)
    assert payload['total_m'] == pytest.approx(
        payload['asphalt_m'] + payload['forest_path_m'] + payload['other_m'],
        abs=0.01,
    )


def test_route_stats_counts_unmatched_segments_as_other(
    authenticated_client: TestClient,
) -> None:
    """Проверить учет маршрута вне опорной сети как `other`."""
    create_response = authenticated_client.post(
        '/api/routes',
        json={
            'name': 'Unmatched stats route',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[0.02, 0.02], [0.021, 0.02]],
            },
        },
    )
    route_id = create_response.json()['id']

    response = authenticated_client.get(f'/api/routes/{route_id}/stats')

    payload = response.json()

    assert response.status_code == 200
    assert payload['asphalt_m'] == 0
    assert payload['forest_path_m'] == 0
    assert payload['field_path_m'] == 0
    assert payload['rail_m'] == 0
    assert payload['other_m'] == pytest.approx(111.32, abs=1)
    assert payload['total_m'] == pytest.approx(payload['other_m'], abs=0.01)


def _insert_reference_segments() -> None:
    """Добавить тестовые опорные сегменты."""
    with SessionLocal() as session:
        session.add_all(
            [
                ReferenceSegment(
                    geometry=_line_string([[0, 0], [0.001, 0]]),
                    surface_class='asphalt',
                ),
                ReferenceSegment(
                    geometry=_line_string([[0.001, 0], [0.002, 0]]),
                    surface_class='forest_path',
                ),
                ReferenceSegment(
                    geometry=_line_string([[0.01, 0], [0.011, 0]]),
                    surface_class='other',
                ),
            ]
        )
        session.commit()


def _line_string(coordinates: list[list[float]]) -> object:
    """Сформировать PostGIS LineString из координат GeoJSON."""
    return func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(
            json.dumps({'type': 'LineString', 'coordinates': coordinates}),
        ),
        4326,
    )
