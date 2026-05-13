"""Схемы объединения маршрутов."""

from uuid import UUID

from pydantic import BaseModel, Field

from may_walk.schemas.geometries import GeoJSONMultiLineStringGeometry


class RouteMergeRequest(BaseModel):
    """Запрос объединения сохраненных маршрутов."""

    route_ids: list[UUID] = Field(
        min_length=1,
        description='Идентификаторы маршрутов для объединения.',
    )


class RouteMergeResponse(BaseModel):
    """Ответ с объединенной геометрией."""

    merged_geometry: GeoJSONMultiLineStringGeometry = Field(
        description='Геометрия после объединения близких и уникальных участков.',
    )
