"""Поиск соответствующих сегментов опорной сети."""

import math

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select

from may_walk.models.reference_segment import ReferenceSegment

REFERENCE_MATCH_TOLERANCE_M = 6.0
REFERENCE_MATCH_TOLERANCE_DEGREES = 0.00008
REFERENCE_MATCH_MAX_ANGLE_DEGREES = 15.0
REFERENCE_MATCH_MAX_ANGLE_RADIANS = math.radians(REFERENCE_MATCH_MAX_ANGLE_DEGREES)


def exact_reference_match(source_segments):
    """Сформировать lateral-запрос точного линейного совпадения."""
    intersection_geometry = func.ST_CollectionExtract(
        func.ST_Intersection(source_segments.c.geometry, ReferenceSegment.geometry),
        2,
    )
    return (
        select(
            ReferenceSegment.surface_class.label('surface_class'),
            ReferenceSegment.geometry.label('reference_geometry'),
        )
        .where(
            source_segments.c.geometry.op('&&')(ReferenceSegment.geometry),
            func.ST_Intersects(source_segments.c.geometry, ReferenceSegment.geometry),
            ~func.ST_IsEmpty(intersection_geometry),
        )
        .order_by(
            func.ST_Length(cast(intersection_geometry, Geography(srid=4326))).desc()
        )
        .limit(1)
        .lateral('exact_reference')
    )


def nearest_reference_match(source_segments, exact_reference=None):
    """Сформировать lateral-запрос ближайшего опорного сегмента."""
    conditions = [
        ReferenceSegment.geometry.op('&&')(
            func.ST_Expand(
                source_segments.c.geometry,
                REFERENCE_MATCH_TOLERANCE_DEGREES,
            )
        ),
        func.ST_DWithin(
            cast(source_segments.c.geometry, Geography(srid=4326)),
            cast(ReferenceSegment.geometry, Geography(srid=4326)),
            REFERENCE_MATCH_TOLERANCE_M,
        ),
    ]
    if exact_reference is not None:
        conditions.append(exact_reference.c.surface_class.is_(None))

    return (
        select(
            ReferenceSegment.surface_class.label('surface_class'),
            ReferenceSegment.geometry.label('reference_geometry'),
        )
        .where(*conditions)
        .order_by(source_segments.c.geometry.op('<->')(ReferenceSegment.geometry))
        .limit(1)
        .lateral('nearest_reference')
    )


def nearest_directional_reference_match(source_segments, exact_reference=None):
    """Сформировать lateral-запрос ближайшего сонаправленного участка дороги."""
    reference_geometry = ReferenceSegment.geometry
    direction_difference = _direction_difference(
        source_segments.c.geometry,
        reference_geometry,
    )
    conditions = [
        func.ST_NPoints(reference_geometry) == 2,
        reference_geometry.op('&&')(
            func.ST_Expand(
                source_segments.c.geometry,
                REFERENCE_MATCH_TOLERANCE_DEGREES,
            )
        ),
        func.ST_DWithin(
            cast(source_segments.c.geometry, Geography(srid=4326)),
            cast(reference_geometry, Geography(srid=4326)),
            REFERENCE_MATCH_TOLERANCE_M,
        ),
        func.ST_DWithin(
            cast(func.ST_StartPoint(source_segments.c.geometry), Geography(srid=4326)),
            cast(reference_geometry, Geography(srid=4326)),
            REFERENCE_MATCH_TOLERANCE_M,
        ),
        func.ST_DWithin(
            cast(func.ST_EndPoint(source_segments.c.geometry), Geography(srid=4326)),
            cast(reference_geometry, Geography(srid=4326)),
            REFERENCE_MATCH_TOLERANCE_M,
        ),
        direction_difference <= REFERENCE_MATCH_MAX_ANGLE_RADIANS,
    ]
    if exact_reference is not None:
        conditions.append(exact_reference.c.surface_class.is_(None))

    return (
        select(
            ReferenceSegment.surface_class.label('surface_class'),
            reference_geometry.label('reference_geometry'),
        )
        .where(*conditions)
        .order_by(
            func.ST_Distance(
                cast(source_segments.c.geometry, Geography(srid=4326)),
                cast(reference_geometry, Geography(srid=4326)),
            ),
            direction_difference,
        )
        .limit(1)
        .lateral('nearest_directional_reference')
    )


def _direction_difference(source_geometry, reference_geometry):
    """Вернуть минимальную разницу направлений двух LineString без учета ориентации."""
    source_azimuth = func.ST_Azimuth(
        func.ST_StartPoint(source_geometry),
        func.ST_EndPoint(source_geometry),
    )
    reference_azimuth = func.ST_Azimuth(
        func.ST_StartPoint(reference_geometry),
        func.ST_EndPoint(reference_geometry),
    )
    directed_difference = func.abs(
        func.pi() - func.abs(func.abs(source_azimuth - reference_azimuth) - func.pi())
    )
    return func.least(directed_difference, func.pi() - directed_difference)
