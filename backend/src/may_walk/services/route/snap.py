"""Примагничивание маршрутов к опорной сети."""

import json

from sqlalchemy import func, select, true
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


def snap_route_geometry(session: Session, geometry: GeoJSONGeometry) -> GeoJSONGeometry:
    """Вернуть геометрию, где найденные участки заменены опорными сегментами."""
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
    snapped_segments = (
        select(
            source_segments.c.path,
            func.coalesce(
                exact_reference.c.reference_geometry,
                nearest_reference.c.reference_geometry,
                source_segments.c.geometry,
            ).label('geometry'),
        )
        .select_from(
            source_segments.outerjoin(exact_reference, true()).outerjoin(
                nearest_reference,
                true(),
            )
        )
        .cte('snapped_segments')
    )
    collected_geometry = func.ST_Multi(
        func.ST_Collect(
            func.array_agg(
                aggregate_order_by(
                    snapped_segments.c.geometry,
                    snapped_segments.c.path,
                )
            )
        )
    )
    return select(func.ST_AsGeoJSON(collected_geometry))


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
