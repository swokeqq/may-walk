"""Расчет статистики маршрутов по опорной сети."""

from dataclasses import dataclass
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select, true
from sqlalchemy.orm import Session

from may_walk.models.route import Route
from may_walk.services.reference_segments.matching import (
    REFERENCE_MATCH_TOLERANCE_DEGREES,
    exact_reference_match,
    nearest_directional_reference_match,
)
from may_walk.services.reference_segments.surface_classes import SURFACE_CLASS_VALUES

ROUTE_STATS_SEGMENTIZE_DEGREES = REFERENCE_MATCH_TOLERANCE_DEGREES / 4


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
    """Посчитать длину сегментов маршрута по покрытиям опорной сети."""
    lengths_by_field = {
        f'{surface_class}_m': 0.0 for surface_class in SURFACE_CLASS_VALUES
    }

    for surface_class, length_m in session.execute(
        _classified_segment_lengths_query(route_id)
    ):
        lengths_by_field[f'{surface_class}_m'] = float(length_m or 0.0)
    total_m = float(session.scalar(_route_total_length_query(route_id)) or 0.0)

    return RouteStats(
        asphalt_m=lengths_by_field['asphalt_m'],
        forest_path_m=lengths_by_field['forest_path_m'],
        field_path_m=lengths_by_field['field_path_m'],
        rail_m=lengths_by_field['rail_m'],
        other_m=lengths_by_field['other_m'],
        total_m=total_m,
    )


def _classified_segment_lengths_query(route_id: UUID):
    """Сформировать запрос классификации сегментов маршрута по опорной сети."""
    route_segments = _route_segments(route_id)
    exact_reference = exact_reference_match(route_segments)
    nearest_reference = nearest_directional_reference_match(
        route_segments,
        exact_reference,
    )
    surface_class = func.coalesce(
        exact_reference.c.surface_class,
        nearest_reference.c.surface_class,
        'other',
    ).label('surface_class')
    classified_segments = (
        select(
            surface_class,
            route_segments.c.geometry.label('geometry'),
        )
        .select_from(
            route_segments.outerjoin(exact_reference, true()).outerjoin(
                nearest_reference,
                true(),
            )
        )
        .cte('classified_segments')
    )
    return select(
        classified_segments.c.surface_class,
        func.sum(
            func.ST_Length(
                cast(classified_segments.c.geometry, Geography(srid=4326)),
            )
        ).label('length_m'),
    ).group_by(classified_segments.c.surface_class)


def _route_segments(route_id: UUID):
    """Сформировать CTE отдельных сегментов маршрута."""
    segment_dump = (
        func.ST_DumpSegments(
            func.ST_Segmentize(Route.geometry, ROUTE_STATS_SEGMENTIZE_DEGREES)
        )
        .table_valued('path', 'geom')
        .lateral('segment_dump')
    )
    return (
        select(segment_dump.c.geom.label('geometry'))
        .select_from(Route)
        .join(segment_dump, true())
        .where(Route.id == route_id, Route.geometry.is_not(None))
        .cte('route_segments')
    )


def _route_total_length_query(route_id: UUID):
    """Сформировать запрос полной длины маршрута по его сегментам."""
    route_segments = _route_segments(route_id)
    return select(
        func.sum(
            func.ST_Length(
                cast(route_segments.c.geometry, Geography(srid=4326)),
            )
        )
    )
