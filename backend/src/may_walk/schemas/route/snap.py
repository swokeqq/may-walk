"""Схемы примагничивания линейной геометрии."""

from pydantic import BaseModel, Field

from may_walk.schemas.geometries import GeoJSONGeometry, GeoJSONMultiLineStringGeometry


class RouteSnapRequest(BaseModel):
    """Запрос примагничивания переданной линии к OSM через OSRM."""

    geometry: GeoJSONGeometry = Field(
        description=(
            'Геометрия для OSRM-примагничивания в EPSG:4326: одна линия `LineString` '
            'или несколько линий `MultiLineString`.'
        ),
    )


class RouteSnapResponse(BaseModel):
    """Ответ с примагниченной геометрией."""

    snapped_geometry: GeoJSONMultiLineStringGeometry = Field(
        description=(
            'Переданная геометрия после OSRM-примагничивания найденных участков.'
        ),
    )
