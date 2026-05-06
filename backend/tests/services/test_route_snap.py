"""Тесты сервиса примагничивания геометрии."""

import json

import pytest
from sqlalchemy import delete, func

from may_walk.db.session import SessionLocal
from may_walk.models.reference_segment import ReferenceSegment
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.route.snap import snap_geometry


@pytest.fixture(autouse=True)
def clean_reference_segments() -> None:
    """Очистить опорные сегменты до и после теста."""
    _delete_reference_segments()
    yield
    _delete_reference_segments()


def test_snap_geometry_returns_nearby_reference_line() -> None:
    """Проверить замену входной линии ближайшим опорным сегментом."""
    _insert_reference_segment([[0, 0], [0.001, 0]])

    with SessionLocal() as session:
        result = snap_geometry(
            session,
            GeoJSONGeometry.model_validate(
                {
                    'type': 'LineString',
                    'coordinates': [[0, 0.00005], [0.001, 0.00005]],
                }
            ),
        )

    assert result.model_dump() == {
        'type': 'MultiLineString',
        'coordinates': [[(0.0, 0.0), (0.001, 0.0)]],
    }


def test_snap_geometry_returns_reference_substring() -> None:
    """Проверить замену линии подотрезком длинного опорного сегмента."""
    _insert_reference_segment([[0, 0], [0.01, 0]])

    with SessionLocal() as session:
        result = snap_geometry(
            session,
            GeoJSONGeometry.model_validate(
                {
                    'type': 'LineString',
                    'coordinates': [[0.003, 0.00005], [0.004, 0.00005]],
                }
            ),
        )

    coordinates = result.model_dump()['coordinates']

    assert result.type == 'MultiLineString'
    assert len(coordinates) == 1
    assert len(coordinates[0]) == 2
    assert coordinates[0][0] == pytest.approx((0.003, 0.0))
    assert coordinates[0][1] == pytest.approx((0.004, 0.0))


def test_snap_geometry_preserves_reverse_direction() -> None:
    """Проверить сохранение обратного направления входной линии."""
    _insert_reference_segment([[0, 0], [0.01, 0]])

    with SessionLocal() as session:
        result = snap_geometry(
            session,
            GeoJSONGeometry.model_validate(
                {
                    'type': 'LineString',
                    'coordinates': [[0.004, 0.00005], [0.003, 0.00005]],
                }
            ),
        )

    coordinates = result.model_dump()['coordinates']

    assert result.type == 'MultiLineString'
    assert len(coordinates) == 1
    assert len(coordinates[0]) == 2
    assert coordinates[0][0] == pytest.approx((0.004, 0.0))
    assert coordinates[0][1] == pytest.approx((0.003, 0.0))


def test_snap_geometry_keeps_line_without_reference_match() -> None:
    """Проверить fallback на исходную линию без найденной дороги."""
    source_geometry = GeoJSONGeometry.model_validate(
        {
            'type': 'LineString',
            'coordinates': [[0.02, 0.02], [0.021, 0.02]],
        }
    )

    with SessionLocal() as session:
        result = snap_geometry(session, source_geometry)

    assert result.model_dump() == {
        'type': 'MultiLineString',
        'coordinates': [[(0.02, 0.02), (0.021, 0.02)]],
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


def _delete_reference_segments() -> None:
    """Удалить тестовые опорные сегменты."""
    with SessionLocal() as session:
        session.execute(delete(ReferenceSegment))
        session.commit()
