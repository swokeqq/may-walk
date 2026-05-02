"""Хранение опорных сегментов в БД."""

from may_walk.services.reference_segments.storage.database import (
    count_reference_segments,
    load_reference_segments,
)
from may_walk.services.reference_segments.storage.result import ImportResult

__all__ = [
    'ImportResult',
    'count_reference_segments',
    'load_reference_segments',
]
