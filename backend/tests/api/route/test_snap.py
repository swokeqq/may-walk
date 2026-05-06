"""Тесты endpoint'а примагничивания геометрии."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func

from may_walk.db.session import SessionLocal
from may_walk.models.reference_segment import ReferenceSegment


def test_route_snap_requires_auth(client: TestClient) -> None:
    """Проверить защиту endpoint'а примагничивания."""
    response = client.post('/api/routes/snap')

    assert response.status_code == 401


def test_route_snap_returns_nearby_reference_line(
    authenticated_client: TestClient,
) -> None:
    """Проверить замену переданной линии ближайшей дорогой."""
    _insert_reference_segment([[0, 0], [0.001, 0]])

    response = authenticated_client.post(
        '/api/routes/snap',
        json={
            'geometry': {
                'type': 'LineString',
                'coordinates': [[0, 0.00005], [0.001, 0.00005]],
            }
        },
    )

    assert response.status_code == 200
    assert response.json()['snapped_geometry'] == {
        'type': 'MultiLineString',
        'coordinates': [[[0, 0], [0.001, 0]]],
    }


def test_route_snap_returns_reference_substring(
    authenticated_client: TestClient,
) -> None:
    """Проверить возврат подотрезка дороги, а не всего опорного сегмента."""
    _insert_reference_segment([[0, 0], [0.01, 0]])

    response = authenticated_client.post(
        '/api/routes/snap',
        json={
            'geometry': {
                'type': 'LineString',
                'coordinates': [[0.003, 0.00005], [0.004, 0.00005]],
            }
        },
    )

    coordinates = response.json()['snapped_geometry']['coordinates']

    assert response.status_code == 200
    assert len(coordinates) == 1
    assert len(coordinates[0]) == 2
    assert coordinates[0][0] == pytest.approx([0.003, 0])
    assert coordinates[0][1] == pytest.approx([0.004, 0])


def test_route_snap_keeps_line_without_reference_match(
    authenticated_client: TestClient,
) -> None:
    """Проверить fallback на исходную линию, если дорога не найдена."""
    geometry = {
        'type': 'LineString',
        'coordinates': [[0.02, 0.02], [0.021, 0.02]],
    }

    response = authenticated_client.post(
        '/api/routes/snap',
        json={'geometry': geometry},
    )

    assert response.status_code == 200
    assert response.json()['snapped_geometry'] == {
        'type': 'MultiLineString',
        'coordinates': [geometry['coordinates']],
    }


def test_route_snap_accepts_multi_line_string(
    authenticated_client: TestClient,
) -> None:
    """Проверить примагничивание нескольких переданных линий."""
    _insert_reference_segment([[0, 0], [0.001, 0]])

    response = authenticated_client.post(
        '/api/routes/snap',
        json={
            'geometry': {
                'type': 'MultiLineString',
                'coordinates': [
                    [[0, 0.00005], [0.001, 0.00005]],
                    [[0.02, 0.02], [0.021, 0.02]],
                ],
            }
        },
    )

    assert response.status_code == 200
    assert response.json()['snapped_geometry'] == {
        'type': 'MultiLineString',
        'coordinates': [
            [[0, 0], [0.001, 0]],
            [[0.02, 0.02], [0.021, 0.02]],
        ],
    }


def _insert_reference_segment(coordinates: list[list[float]]) -> None:
    """Добавить тестовый опорный сегмент."""
    with SessionLocal() as session:
        session.add(
            ReferenceSegment(
                geometry=_line_string(coordinates),
                surface_class='asphalt',
            )
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
