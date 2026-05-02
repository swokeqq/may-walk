"""Классы покрытий опорных сегментов."""

from typing import Literal

SurfaceClass = Literal['asphalt', 'forest_path', 'field_path', 'rail', 'other']
SURFACE_CLASS_VALUES: tuple[SurfaceClass, ...] = (
    'asphalt',
    'forest_path',
    'field_path',
    'rail',
    'other',
)
