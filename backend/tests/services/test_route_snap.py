"""Тесты сервиса примагничивания геометрии через OSRM."""

import pytest
import respx
from httpx import Response

from may_walk.core.settings import settings
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.route.snap import snap_geometry

_OSRM_URL = 'http://osrm:5000'


def _osrm_ok(*lines: list[list[float]]) -> dict:
    """Сформировать успешный ответ OSRM /match с переданными линиями."""
    return {
        'code': 'Ok',
        'matchings': [
            {'geometry': {'type': 'LineString', 'coordinates': coords}}
            for coords in lines
        ],
    }


@respx.mock
def test_snap_geometry_returns_osrm_matched_geometry() -> None:
    """Проверить возврат примагниченной геометрии из ответа OSRM."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        return_value=Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]]))
    )

    result = snap_geometry(
        GeoJSONGeometry.model_validate(
            {'type': 'LineString', 'coordinates': [[0, 0.00005], [0.001, 0.00005]]}
        ),
    )

    coordinates = result.model_dump()['coordinates']
    assert result.type == 'MultiLineString'
    assert len(coordinates) == 1
    assert coordinates[0][0] == pytest.approx((0.0, 0.0), abs=1e-5)
    assert coordinates[0][1] == pytest.approx((0.001, 0.0), abs=1e-5)


@respx.mock
def test_snap_geometry_falls_back_on_osrm_error() -> None:
    """Проверить fallback на исходную геометрию при HTTP-ошибке OSRM."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(return_value=Response(500))

    source_coords = [[0.02, 0.02], [0.021, 0.02]]
    result = snap_geometry(
        GeoJSONGeometry.model_validate(
            {'type': 'LineString', 'coordinates': source_coords}
        ),
    )

    coordinates = result.model_dump()['coordinates']
    assert result.type == 'MultiLineString'
    assert len(coordinates) == 1
    assert coordinates[0][0] == pytest.approx((0.02, 0.02))
    assert coordinates[0][1] == pytest.approx((0.021, 0.02))


@respx.mock
def test_snap_geometry_falls_back_on_osrm_no_match() -> None:
    """Проверить fallback при code != 'Ok' в ответе OSRM."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        return_value=Response(200, json={'code': 'NoMatch'})
    )

    source_coords = [[0.02, 0.02], [0.021, 0.02]]
    result = snap_geometry(
        GeoJSONGeometry.model_validate(
            {'type': 'LineString', 'coordinates': source_coords}
        ),
    )

    coordinates = result.model_dump()['coordinates']
    assert result.type == 'MultiLineString'
    assert len(coordinates) == 1
    assert coordinates[0][0] == pytest.approx((0.02, 0.02))
    assert coordinates[0][1] == pytest.approx((0.021, 0.02))


@respx.mock
def test_snap_geometry_falls_back_on_malformed_osrm_response() -> None:
    """Проверить fallback при неожиданной структуре ответа OSRM."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        return_value=Response(200, json={'code': 'Ok'})
    )
    source_coords = [[0.02, 0.02], [0.021, 0.02]]

    result = snap_geometry(
        GeoJSONGeometry.model_validate(
            {'type': 'LineString', 'coordinates': source_coords}
        ),
    )

    assert result.model_dump()['coordinates'] == [[(0.02, 0.02), (0.021, 0.02)]]


@respx.mock
def test_snap_geometry_assembles_multilinestring_from_gaps() -> None:
    """Проверить сборку MultiLineString из нескольких matchings (разрыв трека)."""
    line1 = [[0.0, 0.0], [0.003, 0.0]]
    line2 = [[0.007, 0.0], [0.01, 0.0]]
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        return_value=Response(200, json=_osrm_ok(line1, line2))
    )

    result = snap_geometry(
        GeoJSONGeometry.model_validate(
            {
                'type': 'LineString',
                'coordinates': [
                    [0.001, 0.00005],
                    [0.002, 0.00005],
                    [0.008, 0.00005],
                    [0.009, 0.00005],
                ],
            }
        ),
    )

    coordinates = result.model_dump()['coordinates']
    assert result.type == 'MultiLineString'
    assert len(coordinates) == 2
    assert coordinates[0][0] == pytest.approx((0.0, 0.0), abs=1e-5)
    assert coordinates[1][-1] == pytest.approx((0.01, 0.0), abs=1e-5)


@respx.mock
def test_snap_geometry_splits_long_line_into_overlapping_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверить разбиение длинной линии по лимиту OSRM /match."""
    monkeypatch.setattr(settings, 'osrm_max_matching_size', 3)
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        side_effect=[
            Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0], [0.002, 0.0]])),
            Response(200, json=_osrm_ok([[0.002, 0.0], [0.003, 0.0], [0.004, 0.0]])),
        ]
    )

    result = snap_geometry(
        GeoJSONGeometry.model_validate(
            {
                'type': 'LineString',
                'coordinates': [
                    [0.0, 0.00005],
                    [0.001, 0.00005],
                    [0.002, 0.00005],
                    [0.003, 0.00005],
                    [0.004, 0.00005],
                ],
            }
        ),
    )

    assert result.model_dump()['coordinates'] == [
        [
            (0.0, 0.0),
            (0.001, 0.0),
            (0.002, 0.0),
            (0.003, 0.0),
            (0.004, 0.0),
        ]
    ]


@respx.mock
def test_snap_geometry_handles_multilinestring_input() -> None:
    """Проверить обработку MultiLineString — каждая линия отдельным запросом."""
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        side_effect=[
            Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]])),
            Response(200, json={'code': 'NoMatch'}),
        ]
    )

    result = snap_geometry(
        GeoJSONGeometry.model_validate(
            {
                'type': 'MultiLineString',
                'coordinates': [
                    [[0, 0.00005], [0.001, 0.00005]],
                    [[0.02, 0.02], [0.021, 0.02]],
                ],
            }
        ),
    )

    coordinates = result.model_dump()['coordinates']
    assert result.type == 'MultiLineString'
    assert len(coordinates) == 2
    assert coordinates[0][0] == pytest.approx((0.0, 0.0), abs=1e-5)
    assert coordinates[0][1] == pytest.approx((0.001, 0.0), abs=1e-5)
    assert coordinates[1][0] == pytest.approx((0.02, 0.02))
    assert coordinates[1][1] == pytest.approx((0.021, 0.02))
