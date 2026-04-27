"""Общие схемы GeoJSON-геометрий."""

from typing import Any, Literal

from pydantic import BaseModel


GeoJSONLineType = Literal['LineString', 'MultiLineString']


class GeoJSONGeometry(BaseModel):
    """GeoJSON геометрия маршрута в EPSG:4326."""

    type: GeoJSONLineType
    coordinates: list[Any]
