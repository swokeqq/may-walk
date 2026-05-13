"""Ошибки объединения маршрутов."""

from uuid import UUID


class RouteMergeError(ValueError):
    """Базовая ошибка объединения маршрутов."""


class RouteMergeInvalidRequestError(RouteMergeError):
    """Некорректный запрос объединения маршрутов."""


class RouteMergeRouteNotFoundError(RouteMergeError):
    """Один из маршрутов для объединения не найден."""

    def __init__(self, route_id: UUID) -> None:
        """Сохранить идентификатор отсутствующего маршрута."""
        super().__init__('Route not found')
        self.route_id = route_id


class RouteMergeRouteWithoutGeometryError(RouteMergeError):
    """Один из маршрутов для объединения не содержит геометрию."""

    def __init__(self, route_id: UUID) -> None:
        """Сохранить идентификатор маршрута без геометрии."""
        super().__init__('Route has no geometry')
        self.route_id = route_id
