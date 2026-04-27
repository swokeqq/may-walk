"""Импорт маршрутов из GPX."""

from xml.etree import ElementTree

from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.route.imports.geometry import multi_line_geometry
from may_walk.services.route.imports.types import RouteImportError
from may_walk.services.route.imports.xml_helpers import find_by_local_name, parse_xml


class GPXImportHandler:
    """Импорт маршрута из GPX."""

    extensions = frozenset({'.gpx'})

    def parse(self, content: bytes) -> GeoJSONGeometry:
        """Извлечь треки и маршруты из GPX."""
        root = parse_xml(content, 'Invalid GPX file')
        lines = []

        for segment in find_by_local_name(root, 'trkseg'):
            line = [
                self._point_from_gpx(point)
                for point in find_by_local_name(segment, 'trkpt')
            ]
            if line:
                lines.append(line)

        route_line = [
            self._point_from_gpx(point) for point in find_by_local_name(root, 'rtept')
        ]
        if route_line:
            lines.append(route_line)

        if not lines:
            raise RouteImportError('GPX file has no route geometry')

        return multi_line_geometry(lines)

    def _point_from_gpx(self, element: ElementTree.Element) -> list[float]:
        """Преобразовать GPX-точку в GeoJSON позицию."""
        try:
            lon = float(element.attrib['lon'])
            lat = float(element.attrib['lat'])
        except (KeyError, ValueError) as error:
            raise RouteImportError('Invalid GPX point') from error

        return [lon, lat]
