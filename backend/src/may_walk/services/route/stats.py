"""Расчет статистики маршрутов по опорной сети."""

from dataclasses import dataclass
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from may_walk.models.reference_segment import ReferenceSegment
from may_walk.models.route import Route
from may_walk.services.reference_segments.surface_classes import SURFACE_CLASS_VALUES


@dataclass(frozen=True)
class RouteStats:
    """Длины маршрута по классам покрытия в метрах."""

    asphalt_m: float
    forest_path_m: float
    field_path_m: float
    rail_m: float
    other_m: float
    total_m: float


def calculate_route_stats(session: Session, route_id: UUID) -> RouteStats:
    """Посчитать длину пересечений маршрута с опорными сегментами по покрытиям."""
    lengths_by_field = {
        f'{surface_class}_m': 0.0 for surface_class in SURFACE_CLASS_VALUES
    }
    intersection_geometry = func.ST_CollectionExtract(
        func.ST_Intersection(Route.geometry, ReferenceSegment.geometry),
        2,
    ).label('geometry')
    intersections = (
        select(
            ReferenceSegment.surface_class.label('surface_class'),
            intersection_geometry,
        )
        .join(
            ReferenceSegment,
            Route.geometry.op('&&')(ReferenceSegment.geometry)
            & func.ST_Intersects(Route.geometry, ReferenceSegment.geometry),
        )
        .where(Route.id == route_id, Route.geometry.is_not(None))
        .cte('intersections')
    )
    route_stats_query = (
        select(
            intersections.c.surface_class,
            func.sum(
                func.ST_Length(
                    cast(intersections.c.geometry, Geography(srid=4326)),
                )
            ).label('length_m'),
        )
        .where(~func.ST_IsEmpty(intersections.c.geometry))
        .group_by(intersections.c.surface_class)
    )

    for surface_class, length_m in session.execute(route_stats_query):
        lengths_by_field[f'{surface_class}_m'] = float(length_m or 0.0)

    return RouteStats(
        asphalt_m=lengths_by_field['asphalt_m'],
        forest_path_m=lengths_by_field['forest_path_m'],
        field_path_m=lengths_by_field['field_path_m'],
        rail_m=lengths_by_field['rail_m'],
        other_m=lengths_by_field['other_m'],
        total_m=sum(lengths_by_field.values()),
    )
