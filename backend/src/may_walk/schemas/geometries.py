"""Общие схемы GeoJSON-геометрий."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

GeoJSONLineType = Literal['LineString', 'MultiLineString']
GeoJSONPosition = Annotated[
    tuple[float, float],
    Field(
        description=(
            'Позиция GeoJSON в системе координат EPSG:4326: '
            '[longitude, latitude].'
        ),
        examples=[[37.6173, 55.7558]],
    ),
]
GeoJSONLineStringCoordinates = Annotated[
    list[GeoJSONPosition],
    Field(
        min_length=2,
        description='Координаты LineString: массив позиций [longitude, latitude].',
        examples=[[[37.6173, 55.7558], [37.618, 55.7562]]],
    ),
]
GeoJSONMultiLineStringCoordinates = Annotated[
    list[GeoJSONLineStringCoordinates],
    Field(
        min_length=1,
        description='Координаты MultiLineString: массив линий LineString.',
        examples=[[[[37.6173, 55.7558], [37.618, 55.7562]]]],
    ),
]


class GeoJSONGeometry(BaseModel):
    """GeoJSON геометрия маршрута в EPSG:4326."""

    model_config = ConfigDict(
        json_schema_extra={
            'description': (
                'GeoJSON LineString или MultiLineString в EPSG:4326. '
                'Порядок координат: [longitude, latitude].'
            ),
            'examples': [
                {
                    'type': 'LineString',
                    'coordinates': [[37.6173, 55.7558], [37.618, 55.7562]],
                },
                {
                    'type': 'MultiLineString',
                    'coordinates': [[[
                        37.6173,
                        55.7558,
                    ], [37.618, 55.7562]]],
                },
            ],
        }
    )

    type: GeoJSONLineType = Field(
        description='Тип GeoJSON-геометрии: LineString или MultiLineString.'
    )
    coordinates: (
        GeoJSONLineStringCoordinates | GeoJSONMultiLineStringCoordinates
    ) = Field(
        description=(
            'Координаты GeoJSON в EPSG:4326. LineString содержит массив позиций, '
            'MultiLineString содержит массив линий.'
        )
    )


class GeoJSONMultiLineStringGeometry(BaseModel):
    """Нормализованная GeoJSON MultiLineString геометрия маршрута."""

    model_config = ConfigDict(
        json_schema_extra={
            'description': (
                'GeoJSON MultiLineString в EPSG:4326. Порядок координат: '
                '[longitude, latitude].'
            ),
            'examples': [
                {
                    'type': 'MultiLineString',
                    'coordinates': [[
                        [37.6173, 55.7558],
                        [37.618, 55.7562],
                    ]],
                }
            ],
        }
    )

    type: Literal['MultiLineString'] = Field(
        description='Тип GeoJSON-геометрии ответа: всегда MultiLineString.'
    )
    coordinates: GeoJSONMultiLineStringCoordinates = Field(
        description=(
            'Координаты MultiLineString в EPSG:4326: массив линий, каждая линия '
            'содержит позиции [longitude, latitude].'
        )
    )
