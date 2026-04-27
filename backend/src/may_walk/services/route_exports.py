"""Сервис экспорта маршрутов в файловые форматы."""

import json
from dataclasses import dataclass
from html import escape
from typing import Any

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.routes import RouteExportFormat


@dataclass(frozen=True)
class RouteExportFile:
    """Содержимое экспортируемого файла маршрута."""

    content: str
    media_type: str
    extension: str


def export_route_file(
    route: Route,
    geometry: GeoJSONGeometry,
    export_format: RouteExportFormat,
) -> RouteExportFile:
    """Сформировать файл маршрута в выбранном формате."""
    match export_format:
        case RouteExportFormat.geojson:
            return _geojson_export_file(route, geometry)
        case RouteExportFormat.gpx:
            return _gpx_export_file(route, geometry)
        case RouteExportFormat.kml:
            return _kml_export_file(route, geometry)

    raise ValueError(f'Unsupported route export format: {export_format}')


def _geojson_export_file(route: Route, geometry: GeoJSONGeometry) -> RouteExportFile:
    """Сформировать GeoJSON-файл маршрута."""
    content = json.dumps(
        {
            'type': 'Feature',
            'properties': {'id': str(route.id), 'name': route.name},
            'geometry': geometry.model_dump(),
        },
        ensure_ascii=False,
    )
    return RouteExportFile(
        content=content,
        media_type='application/geo+json',
        extension='geojson',
    )


def _gpx_export_file(route: Route, geometry: GeoJSONGeometry) -> RouteExportFile:
    """Сформировать GPX-файл маршрута."""
    segments = []
    for line in _multi_line_coordinates(geometry):
        points = ''.join(
            f'<trkpt lat="{lat}" lon="{lon}"></trkpt>' for lon, lat in line
        )
        segments.append(f'<trkseg>{points}</trkseg>')

    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<gpx version="1.1" creator="May Walk" '
        'xmlns="http://www.topografix.com/GPX/1/1">'
        f'<trk><name>{escape(route.name)}</name>{"".join(segments)}</trk>'
        '</gpx>'
    )
    return RouteExportFile(
        content=content,
        media_type='application/gpx+xml',
        extension='gpx',
    )


def _kml_export_file(route: Route, geometry: GeoJSONGeometry) -> RouteExportFile:
    """Сформировать KML-файл маршрута."""
    line_strings = []
    for line in _multi_line_coordinates(geometry):
        coordinates = ' '.join(f'{lon},{lat},0' for lon, lat in line)
        line_strings.append(f'<LineString><coordinates>{coordinates}</coordinates></LineString>')

    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2">'
        '<Document>'
        f'<Placemark><name>{escape(route.name)}</name>'
        f'<MultiGeometry>{"".join(line_strings)}</MultiGeometry>'
        '</Placemark>'
        '</Document>'
        '</kml>'
    )
    return RouteExportFile(
        content=content,
        media_type='application/vnd.google-earth.kml+xml',
        extension='kml',
    )


def _multi_line_coordinates(geometry: GeoJSONGeometry) -> list[Any]:
    """Вернуть координаты MultiLineString."""
    return geometry.model_dump()['coordinates']
