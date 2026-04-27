"""Общие типы импорта маршрутов."""

from typing import Protocol

from may_walk.schemas.geometries import GeoJSONGeometry


class RouteImportError(ValueError):
    """Ошибка импорта маршрута."""


class RouteImportHandler(Protocol):
    """Обработчик импорта маршрута из одного файлового формата."""

    extensions: frozenset[str]

    def parse(self, content: bytes) -> GeoJSONGeometry:
        """Преобразовать содержимое файла в GeoJSON-геометрию."""
