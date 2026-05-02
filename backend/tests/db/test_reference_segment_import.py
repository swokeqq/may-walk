"""Интеграционные тесты загрузки опорных сегментов."""

import json

import pytest
from sqlalchemy import delete, func, select

from may_walk.db.session import SessionLocal
from may_walk.models.reference_segment import ReferenceSegment
from may_walk.services.reference_segments.imports.geojson import (
    parse_reference_segments_content,
)
from may_walk.services.reference_segments.imports.parsed_segments import (
    ReferenceSegmentImportError,
)
from may_walk.services.reference_segments.storage import load_reference_segments


@pytest.fixture(autouse=True)
def clean_reference_segment_table() -> None:
    """Очистить `reference_segment` до и после теста."""
    _delete_reference_segments()
    yield
    _delete_reference_segments()


def test_load_reference_segments_inserts_segments() -> None:
    """Проверить вставку подготовленных сегментов в PostGIS."""
    parse_result = parse_reference_segments_content(
        json.dumps(
            {
                'type': 'FeatureCollection',
                'features': [
                    _feature(
                        {'highway': 'footway', 'surface': 'asphalt'},
                        [[60.6, 56.83], [60.61, 56.834]],
                    ),
                    _feature(
                        {'highway': 'track'},
                        [[60.62, 56.835], [60.63, 56.836]],
                    ),
                ],
            }
        )
    )

    with SessionLocal() as session:
        import_result = load_reference_segments(session, parse_result)
        session.commit()

    rows = _reference_segment_rows()
    assert import_result.inserted_segment_count == 2
    assert import_result.surface_class_counts == {'asphalt': 1, 'field_path': 1}
    assert [row.surface_class for row in rows] == ['asphalt', 'field_path']
    assert json.loads(rows[0].geometry)['coordinates'] == [
        [60.6, 56.83],
        [60.61, 56.834],
    ]


def test_load_reference_segments_requires_replace_for_non_empty_table() -> None:
    """Проверить защиту от смешивания двух опорных слоев."""
    first_parse_result = _parse_single_segment('path')
    second_parse_result = _parse_single_segment('track')

    with SessionLocal() as session:
        load_reference_segments(session, first_parse_result)
        session.commit()

    with SessionLocal() as session:
        with pytest.raises(ReferenceSegmentImportError):
            load_reference_segments(session, second_parse_result)

    with SessionLocal() as session:
        import_result = load_reference_segments(
            session,
            second_parse_result,
            replace=True,
        )
        session.commit()

    assert import_result.inserted_segment_count == 1
    assert [row.surface_class for row in _reference_segment_rows()] == ['field_path']


def _parse_single_segment(highway: str) -> object:
    """Вернуть результат разбора одного тестового сегмента."""
    return parse_reference_segments_content(
        json.dumps(
            _feature(
                {'highway': highway},
                [[60.6, 56.83], [60.61, 56.834]],
            )
        )
    )


def _reference_segment_rows() -> list[object]:
    """Вернуть строки `reference_segment` с GeoJSON-геометрией."""
    with SessionLocal() as session:
        rows = session.execute(
            select(
                ReferenceSegment.surface_class,
                func.ST_AsGeoJSON(ReferenceSegment.geometry),
            ).order_by(ReferenceSegment.id)
        ).all()

    return [
        type('ReferenceSegmentRow', (), {'surface_class': row[0], 'geometry': row[1]})
        for row in rows
    ]


def _feature(
    tags: dict[str, object],
    coordinates: list[list[float]],
) -> dict[str, object]:
    """Создать GeoJSON Feature с LineString."""
    return {
        'type': 'Feature',
        'properties': tags,
        'geometry': {'type': 'LineString', 'coordinates': coordinates},
    }


def _delete_reference_segments() -> None:
    """Удалить опорные сегменты теста."""
    with SessionLocal() as session:
        session.execute(delete(ReferenceSegment))
        session.commit()
