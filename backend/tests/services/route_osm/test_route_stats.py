"""Тесты сервиса статистики маршрутов."""

import json
from uuid import UUID

import pytest
from sqlalchemy import delete, func

from may_walk.db.session import SessionLocal
from may_walk.models.reference_segment import ReferenceSegment
from may_walk.models.route import Route
from may_walk.services.route_osm.stats import calculate_route_stats

# Идентификаторы строк, вставленных в рамках текущего теста.
_test_segment_ids: list[UUID] = []
_test_route_ids: list[UUID] = []


@pytest.fixture(autouse=True)
def clean_route_stats_tables() -> None:
    """Удалить только те строки, которые вставил текущий тест."""
    _delete_test_rows()
    _test_segment_ids.clear()
    _test_route_ids.clear()
    yield
    _delete_test_rows()
    _test_segment_ids.clear()
    _test_route_ids.clear()


def test_calculate_route_stats_groups_exact_matches_by_surface_class() -> None:
    """Проверить группировку точных совпадений по покрытиям."""
    _insert_reference_segment([[0, 0], [0.001, 0]], 'asphalt')
    _insert_reference_segment([[0.001, 0], [0.002, 0]], 'forest_path')
    route_id = _insert_route([[0, 0], [0.001, 0], [0.002, 0]])

    with SessionLocal() as session:
        stats = calculate_route_stats(session, route_id)

    assert stats.asphalt_m == pytest.approx(111.32, abs=1)
    assert stats.forest_path_m == pytest.approx(111.32, abs=1)
    assert stats.field_path_m == 0
    assert stats.rail_m == 0
    assert stats.other_m == 0
    assert stats.total_m == pytest.approx(
        stats.asphalt_m + stats.forest_path_m,
        abs=0.01,
    )


def test_calculate_route_stats_splits_sparse_route_by_reference_segments() -> None:
    """Проверить классификацию длинного сегмента по нескольким покрытиям."""
    _insert_reference_segment([[0, 0], [0.001, 0]], 'asphalt')
    _insert_reference_segment([[0.001, 0], [0.002, 0]], 'forest_path')
    route_id = _insert_route([[0, 0], [0.002, 0]])

    with SessionLocal() as session:
        stats = calculate_route_stats(session, route_id)

    assert stats.asphalt_m == pytest.approx(111.32, abs=1)
    assert stats.forest_path_m == pytest.approx(111.32, abs=1)
    assert stats.total_m == pytest.approx(
        stats.asphalt_m + stats.forest_path_m,
        abs=0.01,
    )


def test_calculate_route_stats_uses_nearby_reference_match() -> None:
    """Проверить классификацию GPS-линии рядом с опорной сетью."""
    _insert_reference_segment([[0, 0], [0.001, 0]], 'asphalt')
    route_id = _insert_route([[0, 0.00005], [0.001, 0.00005]])

    with SessionLocal() as session:
        stats = calculate_route_stats(session, route_id)

    assert stats.asphalt_m == pytest.approx(111.32, abs=1)
    assert stats.forest_path_m == 0
    assert stats.field_path_m == 0
    assert stats.rail_m == 0
    assert stats.other_m == 0
    assert stats.total_m == pytest.approx(stats.asphalt_m, abs=0.01)


def test_calculate_route_stats_counts_unmatched_segments_as_other() -> None:
    """Проверить учет несопоставленной линии как `other`."""
    route_id = _insert_route([[0.02, 0.02], [0.021, 0.02]])

    with SessionLocal() as session:
        stats = calculate_route_stats(session, route_id)

    assert stats.asphalt_m == 0
    assert stats.forest_path_m == 0
    assert stats.field_path_m == 0
    assert stats.rail_m == 0
    assert stats.other_m == pytest.approx(111.32, abs=1)
    assert stats.total_m == pytest.approx(stats.other_m, abs=0.01)


def _insert_route(coordinates: list[list[float]]) -> UUID:
    """Добавить тестовый маршрут и вернуть его id."""
    with SessionLocal() as session:
        route = Route(
            name='Stats service route',
            geometry=func.ST_Multi(_line_string(coordinates)),
        )
        session.add(route)
        session.commit()
        _test_route_ids.append(route.id)
        return route.id


def _insert_reference_segment(
    coordinates: list[list[float]],
    surface_class: str,
) -> None:
    """Добавить тестовый опорный сегмент."""
    with SessionLocal() as session:
        seg = ReferenceSegment(
            geometry=_line_string(coordinates),
            surface_class=surface_class,
        )
        session.add(seg)
        session.commit()
        _test_segment_ids.append(seg.id)


def _line_string(coordinates: list[list[float]]) -> object:
    """Сформировать PostGIS LineString из координат GeoJSON."""
    return func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(
            json.dumps({'type': 'LineString', 'coordinates': coordinates}),
        ),
        4326,
    )


def _delete_test_rows() -> None:
    """Удалить только строки, вставленные текущим тестом."""
    with SessionLocal() as session:
        if _test_segment_ids:
            session.execute(
                delete(ReferenceSegment).where(
                    ReferenceSegment.id.in_(_test_segment_ids)
                )
            )
        if _test_route_ids:
            session.execute(delete(Route).where(Route.id.in_(_test_route_ids)))
        session.commit()
