"""Классификация OSM-тегов опорных сегментов."""

from may_walk.services.reference_segments.classification.classifier import (
    classify_reference_segment,
    normalize_osm_tags,
)

__all__ = [
    'classify_reference_segment',
    'normalize_osm_tags',
]
