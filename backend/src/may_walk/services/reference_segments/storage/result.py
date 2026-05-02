"""Результат импорта опорных сегментов."""

from dataclasses import dataclass

from may_walk.services.reference_segments.surface_classes import SurfaceClass


@dataclass(frozen=True)
class ImportResult:
    """Результат импорта опорных сегментов в БД."""

    inserted_segment_count: int
    skipped_feature_count: int
    surface_class_counts: dict[SurfaceClass, int]
