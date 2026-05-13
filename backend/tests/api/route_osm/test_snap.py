"""Тесты endpoint'а примагничивания геометрии."""

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

_OSRM_URL = 'http://osrm:5000'


def _osrm_ok(*lines: list[list[float]]) -> dict:
    return {
        'code': 'Ok',
        'matchings': [
            {'geometry': {'type': 'LineString', 'coordinates': coords}}
            for coords in lines
        ],
    }


def test_route_snap_requires_auth(client: TestClient) -> None:
    """Проверить защиту endpoint'а примагничивания."""
    response = client.post('/api/routes/snap')

    assert response.status_code == 401


@respx.mock
def test_route_snap_returns_nearby_reference_line(
    authenticated_client: TestClient,
) -> None:
    """Проверить замену переданной линии ближайшей дорогой."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        return_value=Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]]))
    )

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
    snapped = response.json()['snapped_geometry']
    assert snapped['type'] == 'MultiLineString'
    coords = snapped['coordinates']
    assert len(coords) == 1
    assert len(coords[0]) == 2
    assert coords[0][0] == pytest.approx([0.0, 0.0], abs=1e-5)
    assert coords[0][1] == pytest.approx([0.001, 0.0], abs=1e-5)


@respx.mock
def test_route_snap_keeps_line_without_reference_match(
    authenticated_client: TestClient,
) -> None:
    """Проверить fallback на исходную линию, если OSRM не нашёл совпадения."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        return_value=Response(200, json={'code': 'NoMatch'})
    )
    geometry = {
        'type': 'LineString',
        'coordinates': [[0.02, 0.02], [0.021, 0.02]],
    }

    response = authenticated_client.post(
        '/api/routes/snap',
        json={'geometry': geometry},
    )

    assert response.status_code == 200
    snapped = response.json()['snapped_geometry']
    assert snapped['type'] == 'MultiLineString'
    coords = snapped['coordinates']
    assert len(coords) == 1
    assert coords[0][0] == pytest.approx([0.02, 0.02])
    assert coords[0][1] == pytest.approx([0.021, 0.02])


@respx.mock
def test_route_snap_accepts_multi_line_string(
    authenticated_client: TestClient,
) -> None:
    """Проверить примагничивание нескольких переданных линий."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        side_effect=[
            Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]])),
            Response(200, json={'code': 'NoMatch'}),
        ]
    )

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
    snapped = response.json()['snapped_geometry']
    assert snapped['type'] == 'MultiLineString'
    coords = snapped['coordinates']
    assert len(coords) == 2
    assert coords[0][0] == pytest.approx([0.0, 0.0], abs=1e-5)
    assert coords[0][1] == pytest.approx([0.001, 0.0], abs=1e-5)
    assert coords[1][0] == pytest.approx([0.02, 0.02])
    assert coords[1][1] == pytest.approx([0.021, 0.02])
