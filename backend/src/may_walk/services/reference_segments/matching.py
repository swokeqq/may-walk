"""Поиск соответствующих сегментов опорной сети."""

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select

from may_walk.models.reference_segment import ReferenceSegment

REFERENCE_MATCH_TOLERANCE_M = 10.0
REFERENCE_MATCH_TOLERANCE_DEGREES = 0.001


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
