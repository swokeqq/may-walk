"""Экспорт маршрутов в KML."""

from html import escape

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.route.files import RouteExportFormat


class KMLExportHandler:
    """Экспорт маршрута в KML."""

    export_format = RouteExportFormat.kml
    extension = 'kml'
    media_type = 'application/vnd.google-earth.kml+xml'

    def export(self, route: Route, geometry: GeoJSONGeometry) -> str:
        """Сформировать KML-файл маршрута."""
        line_strings = []
        for line in self._multi_line_coordinates(geometry):
            coordinates = ' '.join(f'{lon},{lat},0' for lon, lat in line)
            line_strings.append(
                f'<LineString><coordinates>{coordinates}</coordinates></LineString>',
            )

        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<kml xmlns="http://www.opengis.net/kml/2.2">'
            '<Document>'
            f'<Placemark><name>{escape(route.name)}</name>'
            f'<MultiGeometry>{"".join(line_strings)}</MultiGeometry>'
            '</Placemark>'
            '</Document>'
            '</kml>'
        )

    def _multi_line_coordinates(self, geometry: GeoJSONGeometry) -> list[object]:
        """Вернуть координаты MultiLineString."""
        return geometry.model_dump()['coordinates']
