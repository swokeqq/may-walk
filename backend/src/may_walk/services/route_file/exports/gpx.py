"""Экспорт маршрутов в GPX."""

from html import escape

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.route.files import RouteExportFormat


class GPXExportHandler:
    """Экспорт маршрута в GPX."""

    export_format = RouteExportFormat.gpx
    extension = 'gpx'
    media_type = 'application/gpx+xml'

    def export(self, route: Route, geometry: GeoJSONGeometry) -> str:
        """Сформировать GPX-файл маршрута."""
        segments = []
        for line in self._multi_line_coordinates(geometry):
            points = ''.join(
                f'<trkpt lat="{lat}" lon="{lon}"></trkpt>' for lon, lat in line
            )
            segments.append(f'<trkseg>{points}</trkseg>')

        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<gpx version="1.1" creator="May Walk" '
            'xmlns="http://www.topografix.com/GPX/1/1">'
            f'<trk><name>{escape(route.name)}</name>{"".join(segments)}</trk>'
            '</gpx>'
        )

    def _multi_line_coordinates(self, geometry: GeoJSONGeometry) -> list[object]:
        """Вернуть координаты MultiLineString."""
        return geometry.model_dump()['coordinates']
