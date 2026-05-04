"""Расчет статистики маршрутов по опорной сети."""

from dataclasses import dataclass
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select, true
from sqlalchemy.orm import Session

from may_walk.models.reference_segment import ReferenceSegment
from may_walk.models.route import Route
from may_walk.services.reference_segments.surface_classes import SURFACE_CLASS_VALUES

REFERENCE_MATCH_TOLERANCE_M = 10.0
REFERENCE_MATCH_TOLERANCE_DEGREES = 0.001


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
    exact_reference = _exact_reference(route_segments)
    nearest_reference = _nearest_reference(route_segments)
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
    return (
        select(
            classified_segments.c.surface_class,
            func.sum(
                func.ST_Length(
                    cast(classified_segments.c.geometry, Geography(srid=4326)),
                )
            ).label('length_m'),
        )
        .group_by(classified_segments.c.surface_class)
    )


def _route_segments(route_id: UUID):
    """Сформировать CTE отдельных сегментов маршрута."""
    segment_dump = (
        func.ST_DumpSegments(Route.geometry)
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


def _exact_reference(route_segments):
    """Сформировать lateral-запрос точного линейного совпадения."""
    intersection_geometry = func.ST_CollectionExtract(
        func.ST_Intersection(route_segments.c.geometry, ReferenceSegment.geometry),
        2,
    )
    return (
        select(ReferenceSegment.surface_class.label('surface_class'))
        .where(
            route_segments.c.geometry.op('&&')(ReferenceSegment.geometry),
            func.ST_Intersects(route_segments.c.geometry, ReferenceSegment.geometry),
            ~func.ST_IsEmpty(intersection_geometry),
        )
        .order_by(
            func.ST_Length(cast(intersection_geometry, Geography(srid=4326))).desc()
        )
        .limit(1)
        .lateral('exact_reference')
    )


def _nearest_reference(route_segments):
    """Сформировать lateral-запрос ближайшего опорного сегмента."""
    return (
        select(ReferenceSegment.surface_class.label('surface_class'))
        .where(
            ReferenceSegment.geometry.op('&&')(
                func.ST_Expand(
                    route_segments.c.geometry,
                    REFERENCE_MATCH_TOLERANCE_DEGREES,
                )
            ),
            func.ST_DWithin(
                cast(route_segments.c.geometry, Geography(srid=4326)),
                cast(ReferenceSegment.geometry, Geography(srid=4326)),
                REFERENCE_MATCH_TOLERANCE_M,
            ),
        )
        .order_by(route_segments.c.geometry.op('<->')(ReferenceSegment.geometry))
        .limit(1)
        .lateral('nearest_reference')
    )
