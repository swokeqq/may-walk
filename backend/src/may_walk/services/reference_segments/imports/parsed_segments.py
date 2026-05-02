"""Структуры данных разбора опорных сегментов."""

from collections import Counter
from dataclasses import dataclass
from typing import TypeAlias

from may_walk.services.reference_segments.surface_classes import SurfaceClass

Position: TypeAlias = tuple[float, float]
LineCoordinates: TypeAlias = tuple[Position, ...]


class ReferenceSegmentImportError(ValueError):
    """Ошибка подготовки опорных сегментов к импорту."""


@dataclass(frozen=True)
class ParsedReferenceSegment:
    """Опорный сегмент, подготовленный из OSM-derived GeoJSON."""

    coordinates: LineCoordinates
    surface_class: SurfaceClass


@dataclass(frozen=True)
class ReferenceSegmentParseResult:
    """Результат разбора файла опорных сегментов."""

    segments: tuple[ParsedReferenceSegment, ...]
    skipped_feature_count: int

    @property
    def segment_count(self) -> int:
        """Вернуть количество подготовленных сегментов."""
        return len(self.segments)

    @property
    def surface_class_counts(self) -> dict[SurfaceClass, int]:
        """Вернуть количество сегментов по классам покрытия."""
        return dict(Counter(segment.surface_class for segment in self.segments))
