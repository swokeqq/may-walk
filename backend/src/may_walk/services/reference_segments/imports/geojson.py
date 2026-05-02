"""Разбор OSM-derived GeoJSON для опорных сегментов."""

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from may_walk.services.reference_segments.classification import (
    classify_reference_segment,
)
from may_walk.services.reference_segments.imports.parsed_segments import (
    LineCoordinates,
    ParsedReferenceSegment,
    Position,
    ReferenceSegmentImportError,
    ReferenceSegmentParseResult,
)


def parse_reference_segments_file(file_path: Path) -> ReferenceSegmentParseResult:
    """Прочитать файл и вернуть подготовленные опорные сегменты."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except OSError as error:
        raise ReferenceSegmentImportError(
            f'Cannot read reference segment file: {file_path}'
        ) from error

    return parse_reference_segments_content(content)


def parse_reference_segments_content(content: str) -> ReferenceSegmentParseResult:
    """Разобрать GeoJSON или GeoJSONSeq и вернуть опорные сегменты."""
    if not content.strip():
        raise ReferenceSegmentImportError('Reference segment file is empty')

    features = _features_from_content(content)
    return _segments_from_features(features)


def _features_from_content(content: str) -> tuple[Mapping[str, Any], ...]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        try:
            return _features_from_geojson_sequence(content)
        except ReferenceSegmentImportError as sequence_error:
            raise ReferenceSegmentImportError(
                'Invalid GeoJSON or GeoJSONSeq reference segment file'
            ) from sequence_error

    try:
        return tuple(_features_from_payload(payload))
    except ReferenceSegmentImportError as error:
        raise ReferenceSegmentImportError(
            'Invalid GeoJSON reference segment file'
        ) from error


def _features_from_geojson_sequence(content: str) -> tuple[Mapping[str, Any], ...]:
    features: list[Mapping[str, Any]] = []
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('\x1e'):
            line = line[1:].strip()

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ReferenceSegmentImportError(
                f'Invalid GeoJSONSeq record at line {line_number}'
            ) from error

        features.extend(_features_from_payload(payload))

    if not features:
        raise ReferenceSegmentImportError('GeoJSONSeq file has no Feature records')

    return tuple(features)


def _features_from_payload(payload: Any) -> Iterable[Mapping[str, Any]]:
    if not isinstance(payload, dict):
        raise ReferenceSegmentImportError('GeoJSON payload must be an object')

    payload_type = payload.get('type')
    if payload_type == 'Feature':
        yield _validated_feature(payload)
        return
    if payload_type == 'FeatureCollection':
        features = payload.get('features')
        if not isinstance(features, list):
            raise ReferenceSegmentImportError('GeoJSON FeatureCollection is invalid')
        for feature in features:
            yield _validated_feature(feature)
        return

    raise ReferenceSegmentImportError('GeoJSON payload has no Feature records')


def _validated_feature(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, dict) or payload.get('type') != 'Feature':
        raise ReferenceSegmentImportError('GeoJSON record must be a Feature')

    return payload


def _segments_from_features(
    features: Iterable[Mapping[str, Any]],
) -> ReferenceSegmentParseResult:
    segments: list[ParsedReferenceSegment] = []
    skipped_feature_count = 0

    for feature in features:
        surface_class = classify_reference_segment(_feature_tags(feature))
        line_coordinates = _feature_line_coordinates(feature)
        if surface_class is None or not line_coordinates:
            skipped_feature_count += 1
            continue

        segments.extend(
            ParsedReferenceSegment(coordinates=line, surface_class=surface_class)
            for line in line_coordinates
        )

    return ReferenceSegmentParseResult(
        segments=tuple(segments),
        skipped_feature_count=skipped_feature_count,
    )


def _feature_tags(feature: Mapping[str, Any]) -> dict[str, object]:
    properties = feature.get('properties')
    if not isinstance(properties, dict):
        return {}

    tags = {
        str(key): value
        for key, value in properties.items()
        if key != 'tags' and not str(key).startswith('@')
    }
    nested_tags = properties.get('tags')
    if isinstance(nested_tags, dict):
        tags.update({str(key): value for key, value in nested_tags.items()})

    return tags


def _feature_line_coordinates(
    feature: Mapping[str, Any],
) -> tuple[LineCoordinates, ...]:
    geometry = feature.get('geometry')
    if not isinstance(geometry, dict):
        return ()

    geometry_type = geometry.get('type')
    coordinates = geometry.get('coordinates')
    if geometry_type == 'LineString':
        line = _line_coordinates(coordinates)
        return (line,) if line is not None else ()
    if geometry_type == 'MultiLineString':
        return _multi_line_coordinates(coordinates)

    return ()


def _multi_line_coordinates(coordinates: Any) -> tuple[LineCoordinates, ...]:
    if not isinstance(coordinates, list | tuple):
        return ()

    lines = []
    for raw_line in coordinates:
        line = _line_coordinates(raw_line)
        if line is not None:
            lines.append(line)

    return tuple(lines)


def _line_coordinates(coordinates: Any) -> LineCoordinates | None:
    if not isinstance(coordinates, list | tuple) or len(coordinates) < 2:
        return None

    positions = []
    for raw_position in coordinates:
        position = _position(raw_position)
        if position is None:
            return None
        positions.append(position)

    return tuple(positions)


def _position(position: Any) -> Position | None:
    if not isinstance(position, list | tuple) or len(position) != 2:
        return None

    lon, lat = position
    if not _is_coordinate(lon) or not _is_coordinate(lat):
        return None
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        return None

    return (float(lon), float(lat))


def _is_coordinate(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
