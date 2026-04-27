"""Валидация импортированных геометрий маршрутов."""

from typing import Any

from pydantic import ValidationError

from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.geometries import GeometryValidationError, normalize_line_geometry
from may_walk.services.route.imports.types import RouteImportError


def multi_line_geometry(lines: list[list[list[float]]]) -> GeoJSONGeometry:
    """Создать нормализованную MultiLineString geometry."""
    return validated_geometry({'type': 'MultiLineString', 'coordinates': lines})


def validated_geometry(payload: dict[str, Any]) -> GeoJSONGeometry:
    """Проверить и нормализовать импортированную геометрию."""
    try:
        geometry = GeoJSONGeometry.model_validate(payload)
        return GeoJSONGeometry.model_validate(normalize_line_geometry(geometry))
    except (GeometryValidationError, ValidationError) as error:
        raise RouteImportError('Invalid route geometry') from error
