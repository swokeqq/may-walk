"""Схемы ендпоинтов маршрутов."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from may_walk.schemas.geometries import GeoJSONGeometry, GeoJSONMultiLineStringGeometry


class RouteCreateRequest(BaseModel):
    """Запрос создания маршрута."""

    name: str = Field(
        min_length=1,
        max_length=200,
        description='Название маршрута.',
        examples=['Маршрут 1'],
    )
    geometry: GeoJSONGeometry | None = Field(
        default=None,
        description='Начальная геометрия маршрута в EPSG:4326.',
    )


class RouteUpdateRequest(BaseModel):
    """Запрос обновления маршрута."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description='Новое название маршрута.',
        examples=['Обновленный маршрут'],
    )
    geometry: GeoJSONGeometry | None = Field(
        default=None,
        description='Новая геометрия маршрута в EPSG:4326.',
    )


class RouteListItemResponse(BaseModel):
    """Маршрут в списке без полной геометрии."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description='Идентификатор маршрута.')
    name: str = Field(description='Название маршрута.', examples=['Маршрут 1'])
    created_at: datetime = Field(
        description='Дата и время создания маршрута.',
        examples=['2026-04-28T12:00:00Z'],
    )
    updated_at: datetime = Field(
        description='Дата и время последнего обновления маршрута.',
        examples=['2026-04-28T12:30:00Z'],
    )


class RouteListResponse(BaseModel):
    """Ответ со списком маршрутов."""

    items: list[RouteListItemResponse]


class RouteResponse(RouteListItemResponse):
    """Ответ с маршрутом и полной геометрией."""

    geometry: GeoJSONMultiLineStringGeometry | None = Field(
        description='Нормализованная геометрия маршрута в EPSG:4326.',
    )


class RouteExportFormat(StrEnum):
    """Поддерживаемые форматы экспорта маршрута."""

    geojson = 'geojson'
    gpx = 'gpx'
    kml = 'kml'
