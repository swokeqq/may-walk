"""Загрузка подготовленных опорных сегментов в PostGIS."""

import json
from collections.abc import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from may_walk.models.reference_segment import ReferenceSegment
from may_walk.services.reference_segments.imports.parsed_segments import (
    LineCoordinates,
    ParsedReferenceSegment,
    ReferenceSegmentImportError,
    ReferenceSegmentParseResult,
)
from may_walk.services.reference_segments.storage.result import ImportResult

LOAD_BATCH_SIZE = 1000


def count_reference_segments(session: Session) -> int:
    """Вернуть количество строк в `reference_segment`."""
    return session.scalar(select(func.count()).select_from(ReferenceSegment)) or 0


def load_reference_segments(
    session: Session,
    parse_result: ReferenceSegmentParseResult,
    *,
    replace: bool = False,
) -> ImportResult:
    """Загрузить сегменты в БД в рамках текущей транзакции."""
    if not parse_result.segments:
        raise ReferenceSegmentImportError(
            'Reference segment file has no importable segments'
        )

    if replace:
        session.execute(delete(ReferenceSegment))
    elif count_reference_segments(session) > 0:
        raise ReferenceSegmentImportError(
            'Reference segment table is not empty; use --replace to replace it'
        )

    _insert_segments(session, parse_result.segments)

    return ImportResult(
        inserted_segment_count=parse_result.segment_count,
        skipped_feature_count=parse_result.skipped_feature_count,
        surface_class_counts=parse_result.surface_class_counts,
    )


def _insert_segments(
    session: Session,
    segments: Iterable[ParsedReferenceSegment],
) -> None:
    batch = []
    for segment in segments:
        batch.append(_reference_segment_model(segment))
        if len(batch) >= LOAD_BATCH_SIZE:
            session.add_all(batch)
            session.flush()
            batch.clear()

    if batch:
        session.add_all(batch)
        session.flush()


def _reference_segment_model(segment: ParsedReferenceSegment) -> ReferenceSegment:
    return ReferenceSegment(
        geometry=_line_coordinates_to_postgis(segment.coordinates),
        surface_class=segment.surface_class,
    )


def _line_coordinates_to_postgis(coordinates: LineCoordinates) -> ColumnElement[object]:
    geometry = {
        'type': 'LineString',
        'coordinates': coordinates,
    }
    return func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geometry)), 4326)
