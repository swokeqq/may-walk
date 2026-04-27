"""Экспорт маршрутов в GeoJSON."""

import json

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.routes import RouteExportFormat


class GeoJSONExportHandler:
    """Экспорт маршрута в GeoJSON."""

    export_format = RouteExportFormat.geojson
    extension = 'geojson'
    media_type = 'application/geo+json'

    def export(self, route: Route, geometry: GeoJSONGeometry) -> str:
        """Сформировать GeoJSON-файл маршрута."""
        return json.dumps(
            {
                'type': 'Feature',
                'properties': {'id': str(route.id), 'name': route.name},
                'geometry': geometry.model_dump(),
            },
            ensure_ascii=False,
        )
