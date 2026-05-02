"""Классификация OSM-тегов для импорта опорных сегментов."""

from collections.abc import Mapping
from typing import Literal

from may_walk.services.reference_segments.osm_tags import (
    ASPHALT_SURFACES,
    EXCLUDED_HIGHWAYS,
    FIELD_PATH_SURFACES,
    FOREST_PATH_HIGHWAYS,
    FOREST_PATH_SURFACES,
    NEGATIVE_ACCESS_VALUES,
    NEGATIVE_FOOT_VALUES,
    POSITIVE_FOOT_VALUES,
    REFERENCE_RAILWAYS,
    ROAD_HIGHWAYS,
    TRACK_HIGHWAYS,
)

SurfaceClass = Literal['asphalt', 'forest_path', 'field_path', 'rail', 'other']


def normalize_osm_tags(tags: Mapping[str, object]) -> dict[str, str]:
    """Вернуть OSM-теги в нижнем регистре без пустых значений."""
    normalized_tags: dict[str, str] = {}
    for raw_key, raw_value in tags.items():
        if raw_value is None:
            continue

        key = str(raw_key).strip().lower()
        value = str(raw_value).strip().lower()
        if key and value:
            normalized_tags[key] = value

    return normalized_tags


def classify_reference_segment(tags: Mapping[str, object]) -> SurfaceClass | None:
    """Вернуть класс покрытия или `None` для неподходящего OSM-объекта."""
    normalized_tags = normalize_osm_tags(tags)

    if not _is_importable_segment(normalized_tags):
        return None
    if _has_any_value(normalized_tags, 'railway', REFERENCE_RAILWAYS):
        return 'rail'

    surface_values = _tag_values(normalized_tags, 'surface')
    highway_values = _tag_values(normalized_tags, 'highway')

    if surface_values & ASPHALT_SURFACES:
        return 'asphalt'
    if highway_values & TRACK_HIGHWAYS:
        return 'field_path'
    if surface_values & FIELD_PATH_SURFACES:
        return 'field_path'
    if highway_values & FOREST_PATH_HIGHWAYS:
        return 'forest_path'
    if surface_values & FOREST_PATH_SURFACES:
        return 'forest_path'
    if highway_values & ROAD_HIGHWAYS:
        return 'asphalt'

    return 'other'


def _is_importable_segment(tags: Mapping[str, str]) -> bool:
    if tags.get('area') == 'yes' or _has_forbidden_access(tags):
        return False
    if _has_any_value(tags, 'highway', EXCLUDED_HIGHWAYS):
        return False
    if _has_reference_highway(tags):
        return True
    if _has_any_value(tags, 'railway', REFERENCE_RAILWAYS):
        return True

    return False


def _has_reference_highway(tags: Mapping[str, str]) -> bool:
    highway_values = _tag_values(tags, 'highway')
    return bool(
        highway_values & (TRACK_HIGHWAYS | FOREST_PATH_HIGHWAYS | ROAD_HIGHWAYS)
    )


def _has_forbidden_access(tags: Mapping[str, str]) -> bool:
    foot_values = _tag_values(tags, 'foot')
    if foot_values & POSITIVE_FOOT_VALUES:
        return False
    if foot_values & NEGATIVE_FOOT_VALUES:
        return True

    return bool(_tag_values(tags, 'access') & NEGATIVE_ACCESS_VALUES)


def _has_any_value(
    tags: Mapping[str, str],
    key: str,
    expected_values: frozenset[str],
) -> bool:
    return bool(_tag_values(tags, key) & expected_values)


def _tag_values(tags: Mapping[str, str], key: str) -> set[str]:
    value = tags.get(key)
    if value is None:
        return set()

    return {part.strip() for part in value.split(';') if part.strip()}
