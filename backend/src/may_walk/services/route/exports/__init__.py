"""Сервис экспорта маршрутов в файловые форматы."""

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.routes import RouteExportFormat
from may_walk.services.route.exports.geojson import GeoJSONExportHandler
from may_walk.services.route.exports.gpx import GPXExportHandler
from may_walk.services.route.exports.kml import KMLExportHandler
from may_walk.services.route.exports.types import RouteExportFile, RouteExportHandler

EXPORT_HANDLERS: dict[RouteExportFormat, RouteExportHandler] = {
    handler.export_format: handler
    for handler in (GeoJSONExportHandler(), GPXExportHandler(), KMLExportHandler())
}


def export_route_file(
    route: Route,
    geometry: GeoJSONGeometry,
    export_format: RouteExportFormat,
) -> RouteExportFile:
    """Сформировать файл маршрута в выбранном формате."""
    handler = EXPORT_HANDLERS.get(export_format)
    if handler is None:
        raise ValueError(f'Unsupported route export format: {export_format}')

    return RouteExportFile(
        content=handler.export(route, geometry),
        media_type=handler.media_type,
        extension=handler.extension,
    )
