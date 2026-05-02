"""Тесты разбора OSM-derived GeoJSON опорных сегментов."""

import json

import pytest

from may_walk.services.reference_segments.imports.geojson import (
    parse_reference_segments_content,
)
from may_walk.services.reference_segments.imports.parsed_segments import (
    ReferenceSegmentImportError,
)


def test_parse_reference_segments_geojson_feature_collection() -> None:
    """Проверить разбор FeatureCollection и MultiLineString."""
    payload = {
        'type': 'FeatureCollection',
        'features': [
            _feature(
                {'highway': 'footway', 'surface': 'asphalt'},
                {'type': 'LineString', 'coordinates': [[60.6, 56.83], [60.61, 56.834]]},
            ),
            _feature(
                {'highway': 'track'},
                {
                    'type': 'MultiLineString',
                    'coordinates': [
                        [[60.62, 56.835], [60.63, 56.836]],
                        [[60.64, 56.837], [60.65, 56.838]],
                    ],
                },
            ),
            _feature(
                {'highway': 'motorway'},
                {'type': 'LineString', 'coordinates': [[60.7, 56.85], [60.71, 56.86]]},
            ),
        ],
    }

    result = parse_reference_segments_content(json.dumps(payload))

    assert result.segment_count == 3
    assert result.skipped_feature_count == 1
    assert result.surface_class_counts == {'asphalt': 1, 'field_path': 2}
    assert result.segments[0].coordinates == ((60.6, 56.83), (60.61, 56.834))


def test_parse_reference_segments_geojson_sequence() -> None:
    """Проверить разбор GeoJSONSeq с обычными и RS-prefixed строками."""
    content = '\n'.join(
        [
            json.dumps(
                _feature(
                    {'tags': {'highway': 'path'}},
                    {
                        'type': 'LineString',
                        'coordinates': [[60.6, 56.83], [60.61, 56.834]],
                    },
                )
            ),
            '\x1e'
            + json.dumps(
                _feature(
                    {'railway': 'disused'},
                    {
                        'type': 'LineString',
                        'coordinates': [[60.7, 56.85], [60.71, 56.86]],
                    },
                )
            ),
        ]
    )

    result = parse_reference_segments_content(content)

    assert result.segment_count == 2
    assert result.surface_class_counts == {'forest_path': 1, 'rail': 1}


def test_parse_reference_segments_rejects_empty_content() -> None:
    """Проверить ошибку для пустого файла."""
    with pytest.raises(ReferenceSegmentImportError):
        parse_reference_segments_content('')


def _feature(
    properties: dict[str, object],
    geometry: dict[str, object],
) -> dict[str, object]:
    """Создать GeoJSON Feature для теста."""
    return {
        'type': 'Feature',
        'properties': properties,
        'geometry': geometry,
    }
