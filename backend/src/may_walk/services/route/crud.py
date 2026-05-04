"""Сервисные операции с маршрутами."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.route.crud import RouteCreateRequest, RouteUpdateRequest
from may_walk.services.geometries import geojson_to_postgis, postgis_geojson_to_schema


@dataclass(frozen=True)
class RouteWithGeometry:
    """Маршрут с декодированной GeoJSON-геометрией."""

    route: Route
    geometry: GeoJSONGeometry | None


def list_routes(session: Session) -> list[Route]:
    """Вернуть маршруты в порядке создания."""
    return list(session.scalars(select(Route).order_by(Route.created_at, Route.id)))


def get_route(session: Session, route_id: UUID) -> Route | None:
    """Вернуть маршрут по id."""
    return session.get(Route, route_id)


def get_route_with_geometry(
    session: Session,
    route_id: UUID,
) -> RouteWithGeometry | None:
    """Вернуть маршрут с GeoJSON-геометрией по id."""
    row = session.execute(
        select(Route, func.ST_AsGeoJSON(Route.geometry)).where(Route.id == route_id),
    ).one_or_none()
    if row is None:
        return None

    route, geometry_json = row
    return RouteWithGeometry(
        route=route,
        geometry=postgis_geojson_to_schema(geometry_json),
    )


def create_route(session: Session, request: RouteCreateRequest) -> Route:
    """Создать маршрут."""
    route = Route(name=request.name)
    if request.geometry is not None:
        route.geometry = geojson_to_postgis(request.geometry)

    session.add(route)
    session.flush()
    session.refresh(route)
    return route


def update_route(
    session: Session,
    route: Route,
    request: RouteUpdateRequest,
) -> Route:
    """Обновить маршрут."""
    if request.name is not None:
        route.name = request.name
    if 'geometry' in request.model_fields_set:
        route.geometry = (
            None if request.geometry is None else geojson_to_postgis(request.geometry)
        )

    session.flush()
    session.refresh(route)
    return route


def delete_route(session: Session, route: Route) -> None:
    """Удалить маршрут."""
    session.delete(route)
    session.flush()
