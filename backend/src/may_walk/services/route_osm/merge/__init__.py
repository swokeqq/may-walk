"""Сервис объединения маршрутов."""

from may_walk.services.route_osm.merge.errors import (
    RouteMergeError,
    RouteMergeInvalidRequestError,
    RouteMergeRouteNotFoundError,
    RouteMergeRouteWithoutGeometryError,
)
from may_walk.services.route_osm.merge.service import merge_routes

__all__ = [
    'RouteMergeError',
    'RouteMergeInvalidRequestError',
    'RouteMergeRouteNotFoundError',
    'RouteMergeRouteWithoutGeometryError',
    'merge_routes',
]
