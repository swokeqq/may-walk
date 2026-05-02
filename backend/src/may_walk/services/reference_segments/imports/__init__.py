"""Импорт подготовленных файлов опорных сегментов."""

from may_walk.services.reference_segments.imports.geojson import (
    parse_reference_segments_content,
    parse_reference_segments_file,
)

__all__ = [
    'parse_reference_segments_content',
    'parse_reference_segments_file',
]
