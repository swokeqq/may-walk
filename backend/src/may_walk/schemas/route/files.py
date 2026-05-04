"""Схемы файловых endpoint'ов маршрутов."""

from enum import StrEnum


class RouteExportFormat(StrEnum):
    """Поддерживаемые форматы экспорта маршрута."""

    geojson = 'geojson'
    gpx = 'gpx'
    kml = 'kml'
