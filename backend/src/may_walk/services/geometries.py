"""Сервисные операции с GeoJSON и PostGIS геометриями."""

import json
from typing import Any

from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement

from may_walk.schemas.geometries import GeoJSONGeometry


class GeometryValidationError(ValueError):
    """Ошибка валидации GeoJSON-геометрии."""


def normalize_line_geometry(geometry: GeoJSONGeometry) -> dict[str, Any]:
    """Проверить GeoJSON и вернуть MultiLineString в EPSG:4326."""
    payload = geometry.model_dump()
    geometry_type = payload['type']
    coordinates = payload['coordinates']

    if geometry_type == 'LineString':
        _validate_line_string_coordinates(coordinates)
        return {'type': 'MultiLineString', 'coordinates': [coordinates]}

    _validate_multi_line_string_coordinates(coordinates)
    return payload


def geojson_to_postgis(geometry: GeoJSONGeometry) -> ColumnElement[Any]:
    """Подготовить выражение PostGIS для сохранения GeoJSON в route.geometry."""
    normalized_geometry = normalize_line_geometry(geometry)
    return func.ST_Multi(
        func.ST_SetSRID(
            func.ST_GeomFromGeoJSON(json.dumps(normalized_geometry)),
            4326,
        ),
    )


def postgis_geojson_to_schema(value: str | None) -> GeoJSONGeometry | None:
    """Преобразовать JSON-строку из ST_AsGeoJSON в схему ответа."""
    if value is None:
        return None

    return GeoJSONGeometry.model_validate_json(value)


def _validate_multi_line_string_coordinates(coordinates: object) -> None:
    """Проверить координаты MultiLineString."""
    if not isinstance(coordinates, list) or not coordinates:
        raise GeometryValidationError(
            'MultiLineString coordinates must be a non-empty list'
        )

    for line in coordinates:
        _validate_line_string_coordinates(line)


def _validate_line_string_coordinates(coordinates: object) -> None:
    """Проверить координаты LineString."""
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise GeometryValidationError('LineString must contain at least two positions')

    for position in coordinates:
        _validate_position(position)


def _validate_position(position: object) -> None:
    """Проверить одну GeoJSON-позицию lon/lat."""
    if not isinstance(position, list | tuple) or len(position) != 2:
        raise GeometryValidationError('Position must contain lon and lat')

    lon, lat = position
    if not isinstance(lon, int | float) or not isinstance(lat, int | float):
        raise GeometryValidationError('Position coordinates must be numbers')
    if not -180 <= lon <= 180:
        raise GeometryValidationError('Longitude must be between -180 and 180')
    if not -90 <= lat <= 90:
        raise GeometryValidationError('Latitude must be between -90 and 90')
