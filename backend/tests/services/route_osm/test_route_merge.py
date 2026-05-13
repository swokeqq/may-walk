"""Тесты сервиса объединения маршрутов."""

import json
from uuid import UUID

import pytest
import respx
from httpx import Response
from sqlalchemy import delete, func

from may_walk.db.session import SessionLocal
from may_walk.models.route import Route
from may_walk.services.route_osm.merge import merge_routes

_OSRM_URL = 'http://osrm:5000'
_test_route_ids: list[UUID] = []


@pytest.fixture(autouse=True)
def clean_route_merge_tables() -> None:
    """Удалить только маршруты, вставленные текущим тестом."""
    _delete_test_rows()
    _test_route_ids.clear()
    yield
    _delete_test_rows()
    _test_route_ids.clear()


@respx.mock
def test_merge_routes_collapses_nearby_snapped_lines() -> None:
    """Проверить схлопывание близких GPS-линий после OSRM-нормализации."""
    first_route_id = _insert_route([[0, 0.00005], [0.001, 0.00005]])
    second_route_id = _insert_route([[0, 0.00004], [0.001, 0.00004]])
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        side_effect=[
            Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]])),
            Response(200, json=_osrm_ok([[0.0, 0.0], [0.001, 0.0]])),
        ]
    )

    with SessionLocal() as session:
        result = merge_routes(session, [first_route_id, second_route_id])

    coordinates = result.model_dump()['coordinates']
    assert result.type == 'MultiLineString'
    assert len(coordinates) == 1
    assert coordinates[0][0] == pytest.approx((0.0, 0.0))
    assert coordinates[0][-1] == pytest.approx((0.001, 0.0))


@respx.mock
def test_merge_routes_keeps_distant_routes_as_separate_components() -> None:
    """Проверить, что далекие маршруты не соединяются линией между собой."""
    first_route_id = _insert_route([[0, 0], [0.001, 0]])
    second_route_id = _insert_route([[0.02, 0.02], [0.021, 0.02]])
    respx.get(url__startswith=f'{_OSRM_URL}/match').mock(
        side_effect=[
            Response(200, json={'code': 'NoMatch'}),
            Response(200, json={'code': 'NoMatch'}),
        ]
    )

    with SessionLocal() as session:
        result = merge_routes(session, [first_route_id, second_route_id])

    coordinates = result.model_dump()['coordinates']
    assert result.type == 'MultiLineString'
    assert len(coordinates) == 2
    assert coordinates[0][0] == pytest.approx((0.0, 0.0))
    assert coordinates[0][-1] == pytest.approx((0.001, 0.0))
    assert coordinates[1][0] == pytest.approx((0.02, 0.02))
    assert coordinates[1][-1] == pytest.approx((0.021, 0.02))


def _insert_route(coordinates: list[list[float]]) -> UUID:
    """Добавить тестовый маршрут и вернуть его id."""
    with SessionLocal() as session:
        route = Route(
            name='Merge service route',
            geometry=func.ST_Multi(_line_string(coordinates)),
        )
        session.add(route)
        session.commit()
        _test_route_ids.append(route.id)
        return route.id


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
        if _test_route_ids:
            session.execute(delete(Route).where(Route.id.in_(_test_route_ids)))
        session.commit()


def _osrm_ok(*lines: list[list[float]]) -> dict:
    """Сформировать успешный ответ OSRM /match с переданными линиями."""
    return {
        'code': 'Ok',
        'matchings': [
            {'geometry': {'type': 'LineString', 'coordinates': coords}}
            for coords in lines
        ],
    }
