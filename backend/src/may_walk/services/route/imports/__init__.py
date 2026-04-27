"""Сервис импорта маршрутов из файлов."""

from pathlib import PurePath

from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.route.imports.geojson import GeoJSONImportHandler
from may_walk.services.route.imports.gpx import GPXImportHandler
from may_walk.services.route.imports.kml import KMLImportHandler
from may_walk.services.route.imports.types import RouteImportError, RouteImportHandler

IMPORT_HANDLERS_BY_EXTENSION: dict[str, RouteImportHandler] = {
    extension: handler
    for handler in (GeoJSONImportHandler(), GPXImportHandler(), KMLImportHandler())
    for extension in handler.extensions
}


def parse_route_file(filename: str, content: bytes) -> GeoJSONGeometry:
    """Преобразовать файл маршрута в GeoJSON-геометрию."""
    extension = PurePath(filename).suffix.lower()
    handler = IMPORT_HANDLERS_BY_EXTENSION.get(extension)
    if handler is None:
        raise RouteImportError('Unsupported route file format')

    return handler.parse(content)
