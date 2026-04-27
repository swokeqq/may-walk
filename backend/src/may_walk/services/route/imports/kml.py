"""Импорт маршрутов из KML."""

from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.route.imports.geometry import multi_line_geometry
from may_walk.services.route.imports.types import RouteImportError
from may_walk.services.route.imports.xml_helpers import (
    find_by_local_name,
    first_by_local_name,
    parse_xml,
)


class KMLImportHandler:
    """Импорт маршрута из KML."""

    extensions = frozenset({'.kml'})

    def parse(self, content: bytes) -> GeoJSONGeometry:
        """Извлечь LineString из KML."""
        root = parse_xml(content, 'Invalid KML file')
        lines = []

        for line_string in find_by_local_name(root, 'LineString'):
            coordinates_element = first_by_local_name(line_string, 'coordinates')
            if coordinates_element is None or coordinates_element.text is None:
                continue

            line = self._parse_kml_coordinates(coordinates_element.text)
            if line:
                lines.append(line)

        if not lines:
            raise RouteImportError('KML file has no route geometry')

        return multi_line_geometry(lines)

    def _parse_kml_coordinates(self, value: str) -> list[list[float]]:
        """Преобразовать KML coordinates в GeoJSON позиции."""
        line = []
        for raw_position in value.split():
            parts = raw_position.split(',')
            if len(parts) < 2:
                raise RouteImportError('Invalid KML coordinates')

            try:
                line.append([float(parts[0]), float(parts[1])])
            except ValueError as error:
                raise RouteImportError('Invalid KML coordinates') from error

        return line
