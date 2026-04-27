"""Общие типы экспорта маршрутов."""

from dataclasses import dataclass
from typing import Protocol

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.routes import RouteExportFormat


@dataclass(frozen=True)
class RouteExportFile:
    """Содержимое экспортируемого файла маршрута."""

    content: str
    media_type: str
    extension: str


class RouteExportHandler(Protocol):
    """Обработчик экспорта маршрута в один файловый формат."""

    export_format: RouteExportFormat
    extension: str
    media_type: str

    def export(self, route: Route, geometry: GeoJSONGeometry) -> str:
        """Сформировать содержимое файла маршрута."""
