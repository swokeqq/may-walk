"""Тесты сервиса статистики маршрутов."""

import json
from uuid import UUID

import pytest
from sqlalchemy import delete, func

from may_walk.db.session import SessionLocal
from may_walk.models.reference_segment import ReferenceSegment
from may_walk.models.route import Route
from may_walk.services.route.stats import calculate_route_stats


@pytest.fixture(autouse=True)
def clean_route_stats_tables() -> None:
    """Очистить маршруты и опорные сегменты до и после теста."""
    _delete_rows()
    yield
    _delete_rows()


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
        return route.id


def _insert_reference_segment(
    coordinates: list[list[float]],
    surface_class: str,
) -> None:
    """Добавить тестовый опорный сегмент."""
    with SessionLocal() as session:
        session.add(
            ReferenceSegment(
                geometry=_line_string(coordinates),
                surface_class=surface_class,
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


def _delete_rows() -> None:
    """Удалить тестовые маршруты и опорные сегменты."""
    with SessionLocal() as session:
        session.execute(delete(ReferenceSegment))
        session.execute(delete(Route))
        session.commit()
