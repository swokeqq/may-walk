"""Загрузка подготовленных опорных сегментов в PostGIS."""

import json
from collections import Counter
from collections.abc import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from may_walk.models.reference_segment import (
    ReferenceSegment,
    ReferenceSegmentImportState,
)
from may_walk.services.reference_segments.imports.parsed_segments import (
    LineCoordinates,
    ParsedReferenceSegment,
    ReferenceSegmentImportError,
    ReferenceSegmentParseResult,
)
from may_walk.services.reference_segments.storage.result import ImportResult

LOAD_BATCH_SIZE = 1000
REFERENCE_IMPORT_STATE_ID = 1


def count_reference_segments(session: Session) -> int:
    """Вернуть количество строк в `reference_segment`."""
    return session.scalar(select(func.count()).select_from(ReferenceSegment)) or 0


def get_reference_import_source_hash(session: Session) -> str | None:
    """Вернуть hash последнего импортированного источника reference_segment."""
    return session.scalar(
        select(ReferenceSegmentImportState.source_hash).where(
            ReferenceSegmentImportState.id == REFERENCE_IMPORT_STATE_ID,
        )
    )


def set_reference_import_source_hash(session: Session, source_hash: str) -> None:
    """Сохранить hash источника последнего импорта reference_segment."""
    statement = insert(ReferenceSegmentImportState).values(
        id=REFERENCE_IMPORT_STATE_ID,
        source_hash=source_hash,
    )
    session.execute(
        statement.on_conflict_do_update(
            index_elements=[ReferenceSegmentImportState.id],
            set_={
                ReferenceSegmentImportState.source_hash: statement.excluded.source_hash,
                ReferenceSegmentImportState.imported_at: func.now(),
            },
        )
    )


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

    inserted_segment_count, surface_class_counts = _insert_segments(
        session,
        parse_result.segments,
    )

    return ImportResult(
        inserted_segment_count=inserted_segment_count,
        skipped_feature_count=parse_result.skipped_feature_count,
        surface_class_counts=dict(surface_class_counts),
    )


def _insert_segments(
    session: Session,
    segments: Iterable[ParsedReferenceSegment],
) -> tuple[int, Counter[str]]:
    batch = []
    inserted_segment_count = 0
    surface_class_counts: Counter[str] = Counter()
    for segment in segments:
        for model in _reference_segment_models(segment):
            batch.append(model)
            inserted_segment_count += 1
            surface_class_counts[segment.surface_class] += 1
            if len(batch) >= LOAD_BATCH_SIZE:
                session.add_all(batch)
                session.flush()
                batch.clear()

    if batch:
        session.add_all(batch)
        session.flush()

    return inserted_segment_count, surface_class_counts


def _reference_segment_models(
    segment: ParsedReferenceSegment,
) -> Iterable[ReferenceSegment]:
    for start, end in zip(segment.coordinates, segment.coordinates[1:]):
        if start == end:
            continue
        yield ReferenceSegment(
            geometry=_line_coordinates_to_postgis((start, end)),
            surface_class=segment.surface_class,
        )


def _line_coordinates_to_postgis(coordinates: LineCoordinates) -> ColumnElement[object]:
    geometry = {
        'type': 'LineString',
        'coordinates': coordinates,
    }
    return func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geometry)), 4326)
