"""Объединение маршрутов с удалением близких дублирующихся участков."""

import json
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.geometries import postgis_geojson_to_schema
from may_walk.services.reference_segments.matching import (
    REFERENCE_MATCH_TOLERANCE_DEGREES,
)
from may_walk.services.route.crud import get_route_with_geometry
from may_walk.services.route_osm.merge.errors import (
    RouteMergeError,
    RouteMergeInvalidRequestError,
    RouteMergeRouteNotFoundError,
    RouteMergeRouteWithoutGeometryError,
)
from may_walk.services.route_osm.snap import snap_geometry


def merge_routes(session: Session, route_ids: Sequence[UUID]) -> GeoJSONGeometry:
    """Объединить маршруты, не соединяя далекие компоненты между собой."""
    if not route_ids:
        raise RouteMergeInvalidRequestError('route_ids must contain at least one route')
    if len(set(route_ids)) != len(route_ids):
        raise RouteMergeInvalidRequestError('route_ids must not contain duplicates')

    geometries = [_load_route_geometry(session, route_id) for route_id in route_ids]
    snapped_geometries = [snap_geometry(geometry) for geometry in geometries]

    merged_geometry = _cleanup_geometry(session, snapped_geometries[0])
    for geometry in snapped_geometries[1:]:
        merged_geometry = _append_non_duplicate_parts(
            session,
            merged_geometry,
            geometry,
        )

    return merged_geometry


def _load_route_geometry(session: Session, route_id: UUID) -> GeoJSONGeometry:
    """Загрузить GeoJSON-геометрию маршрута."""
    route_with_geometry = get_route_with_geometry(session, route_id)
    if route_with_geometry is None:
        raise RouteMergeRouteNotFoundError(route_id)
    if route_with_geometry.geometry is None:
        raise RouteMergeRouteWithoutGeometryError(route_id)

    return route_with_geometry.geometry


def _append_non_duplicate_parts(
    session: Session,
    base_geometry: GeoJSONGeometry,
    next_geometry: GeoJSONGeometry,
) -> GeoJSONGeometry:
    """Добавить к результату только участки вне допуска к текущей геометрии."""
    base = _geojson_to_postgis(base_geometry)
    next_ = _geojson_to_postgis(next_geometry)
    unique_next = func.ST_CollectionExtract(
        func.ST_Difference(
            next_,
            func.ST_Buffer(base, REFERENCE_MATCH_TOLERANCE_DEGREES),
        ),
        2,
    )
    merged = _clean_postgis_geometry(func.ST_Collect(base, unique_next))
    return _postgis_expression_to_geojson(session, merged)


def _cleanup_geometry(
    session: Session,
    geometry: GeoJSONGeometry,
) -> GeoJSONGeometry:
    """Нормализовать результат PostGIS-операций в MultiLineString."""
    return _postgis_expression_to_geojson(
        session,
        _clean_postgis_geometry(_geojson_to_postgis(geometry)),
    )


def _geojson_to_postgis(geometry: GeoJSONGeometry):
    """Преобразовать GeoJSON в PostGIS-выражение."""
    return func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(json.dumps(geometry.model_dump())),
        4326,
    )


def _clean_postgis_geometry(geometry):
    """Оставить линейные части и схлопнуть точные дубли."""
    return func.ST_Multi(
        func.ST_LineMerge(
            func.ST_UnaryUnion(
                func.ST_CollectionExtract(geometry, 2),
            )
        )
    )


def _postgis_expression_to_geojson(session: Session, geometry) -> GeoJSONGeometry:
    """Выполнить PostGIS-выражение и вернуть GeoJSON-схему."""
    geometry_json = session.scalar(select(func.ST_AsGeoJSON(geometry)))
    result = postgis_geojson_to_schema(geometry_json)
    if result is None:
        raise RouteMergeError('Merged geometry is empty')

    return result
