"""Примагничивание линейных геометрий к опорной сети."""

import json

from sqlalchemy import case, func, select, true
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import Session

from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.geometries import (
    normalize_line_geometry,
    postgis_geojson_to_schema,
)
from may_walk.services.reference_segments.matching import (
    exact_reference_match,
    nearest_reference_match,
)


def snap_geometry(session: Session, geometry: GeoJSONGeometry) -> GeoJSONGeometry:
    """Вернуть переданную геометрию с заменой найденных участков дорогами."""
    snapped_geometry_json = session.scalar(_snapped_geometry_query(geometry))
    snapped_geometry = postgis_geojson_to_schema(snapped_geometry_json)
    if snapped_geometry is None:
        return GeoJSONGeometry.model_validate(normalize_line_geometry(geometry))

    return snapped_geometry


def _snapped_geometry_query(geometry: GeoJSONGeometry):
    """Сформировать запрос примагничивания GeoJSON-геометрии."""
    source_segments = _source_segments(geometry)
    exact_reference = exact_reference_match(source_segments)
    nearest_reference = nearest_reference_match(source_segments, exact_reference)
    matched_segments = (
        select(
            source_segments.c.path,
            source_segments.c.geometry.label('source_geometry'),
            func.coalesce(
                exact_reference.c.reference_geometry,
                nearest_reference.c.reference_geometry,
            ).label('reference_geometry'),
        )
        .select_from(
            source_segments.outerjoin(exact_reference, true()).outerjoin(
                nearest_reference,
                true(),
            )
        )
        .cte('matched_segments')
    )
    snapped_segments = (
        select(
            matched_segments.c.path,
            _snapped_segment_geometry(
                matched_segments.c.source_geometry,
                matched_segments.c.reference_geometry,
            ).label('geometry'),
        )
        .select_from(matched_segments)
        .cte('snapped_segments')
    )
    collected_geometry = func.ST_Multi(
        func.ST_CollectionExtract(
            func.ST_Collect(
                func.array_agg(
                    aggregate_order_by(
                        snapped_segments.c.geometry,
                        snapped_segments.c.path,
                    )
                )
            ),
            2,
        )
    )
    return select(func.ST_AsGeoJSON(collected_geometry))


def _snapped_segment_geometry(source_geometry, reference_geometry):
    """Вернуть подотрезок опорного сегмента для входного участка."""
    start_fraction = func.ST_LineLocatePoint(
        reference_geometry,
        func.ST_StartPoint(source_geometry),
    )
    end_fraction = func.ST_LineLocatePoint(
        reference_geometry,
        func.ST_EndPoint(source_geometry),
    )
    forward_geometry = func.ST_LineSubstring(
        reference_geometry,
        start_fraction,
        end_fraction,
    )
    reversed_geometry = func.ST_Reverse(
        func.ST_LineSubstring(
            reference_geometry,
            end_fraction,
            start_fraction,
        )
    )
    return case(
        (reference_geometry.is_(None), source_geometry),
        (start_fraction == end_fraction, source_geometry),
        (start_fraction <= end_fraction, forward_geometry),
        else_=reversed_geometry,
    )


def _source_segments(geometry: GeoJSONGeometry):
    """Сформировать CTE отдельных сегментов входной GeoJSON-геометрии."""
    normalized_geometry = normalize_line_geometry(geometry)
    source_geometry = func.ST_Multi(
        func.ST_SetSRID(
            func.ST_GeomFromGeoJSON(json.dumps(normalized_geometry)),
            4326,
        )
    )
    segment_dump = (
        func.ST_DumpSegments(source_geometry)
        .table_valued('path', 'geom')
        .lateral('segment_dump')
    )
    return select(
        segment_dump.c.path.label('path'),
        segment_dump.c.geom.label('geometry'),
    ).cte('source_segments')
