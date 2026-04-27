"""Схемы ендпоинтов маршрутов."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from may_walk.schemas.geometries import GeoJSONGeometry


class RouteCreateRequest(BaseModel):
    """Запрос создания маршрута."""

    name: str = Field(min_length=1, max_length=200)
    geometry: GeoJSONGeometry | None = None


class RouteUpdateRequest(BaseModel):
    """Запрос обновления маршрута."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    geometry: GeoJSONGeometry | None = None


class RouteListItemResponse(BaseModel):
    """Маршрут в списке без полной геометрии."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class RouteListResponse(BaseModel):
    """Ответ со списком маршрутов."""

    items: list[RouteListItemResponse]


class RouteResponse(RouteListItemResponse):
    """Ответ с маршрутом и полной геометрией."""

    geometry: GeoJSONGeometry | None


class RouteExportFormat(StrEnum):
    """Поддерживаемые форматы экспорта маршрута."""

    geojson = 'geojson'
    gpx = 'gpx'
    kml = 'kml'
