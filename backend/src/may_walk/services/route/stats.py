"""Расчет статистики маршрутов по опорной сети."""

from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from may_walk.models.reference_segment import ReferenceSegment
from may_walk.models.route import Route
from may_walk.services.reference_segments.surface_classes import SURFACE_CLASS_VALUES


def calculate_route_stats(session: Session, route_id: UUID) -> dict[str, float]:
    """Посчитать длину пересечений маршрута с опорными сегментами по покрытиям."""
    stats = {f'{surface_class}_m': 0.0 for surface_class in SURFACE_CLASS_VALUES}
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
        stats[f'{surface_class}_m'] = float(length_m or 0.0)

    stats['total_m'] = sum(stats.values())
    return stats
