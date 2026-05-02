"""Тесты классификации OSM-тегов опорных сегментов."""

import pytest

from may_walk.services.reference_segments.classification import (
    classify_reference_segment,
)


@pytest.mark.parametrize(
    ('tags', 'expected_surface_class'),
    [
        ({'highway': 'residential'}, 'asphalt'),
        ({'highway': 'footway', 'surface': 'asphalt'}, 'asphalt'),
        ({'highway': 'path'}, 'forest_path'),
        ({'highway': 'track'}, 'field_path'),
        ({'railway': 'disused'}, 'rail'),
        ({'highway': 'service', 'surface': 'gravel'}, 'field_path'),
    ],
)
def test_classify_reference_segment_returns_surface_class(
    tags: dict[str, object],
    expected_surface_class: str,
) -> None:
    """Проверить классификацию подходящих OSM-объектов."""
    assert classify_reference_segment(tags) == expected_surface_class


@pytest.mark.parametrize(
    'tags',
    [
        {'highway': 'motorway'},
        {'highway': 'path', 'access': 'no'},
        {'highway': 'footway', 'foot': 'no'},
        {'highway': 'service', 'area': 'yes'},
        {'building': 'yes'},
    ],
)
def test_classify_reference_segment_skips_unsuitable_objects(
    tags: dict[str, object],
) -> None:
    """Проверить отбрасывание неподходящих OSM-объектов."""
    assert classify_reference_segment(tags) is None


def test_classify_reference_segment_allows_positive_foot_access() -> None:
    """Проверить приоритет явного разрешения `foot` над общим `access`."""
    assert (
        classify_reference_segment(
            {'highway': 'path', 'access': 'no', 'foot': 'yes'},
        )
        == 'forest_path'
    )
