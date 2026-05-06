"""Схемы примагничивания линейной геометрии."""

from pydantic import BaseModel, Field

from may_walk.schemas.geometries import GeoJSONGeometry, GeoJSONMultiLineStringGeometry


class RouteSnapRequest(BaseModel):
    """Запрос примагничивания переданной линии к опорной сети."""

    geometry: GeoJSONGeometry = Field(
        description=(
            'Геометрия для примагничивания в EPSG:4326: одна линия `LineString` '
            'или несколько линий `MultiLineString`.'
        ),
    )


class RouteSnapResponse(BaseModel):
    """Ответ с примагниченной геометрией."""

    snapped_geometry: GeoJSONMultiLineStringGeometry = Field(
        description='Переданная геометрия после замены найденных участков дорогами.',
    )
