"""Общие сборщики ответов route API."""

from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry, GeoJSONMultiLineStringGeometry
from may_walk.schemas.routes import RouteResponse


def route_response(route: Route, geometry: GeoJSONGeometry | None) -> RouteResponse:
    """Собрать API-ответ маршрута с нормализованной геометрией ответа."""
    response_geometry = None
    if geometry is not None:
        response_geometry = GeoJSONMultiLineStringGeometry.model_validate(
            geometry.model_dump()
        )

    return RouteResponse(
        id=route.id,
        name=route.name,
        geometry=response_geometry,
        created_at=route.created_at,
        updated_at=route.updated_at,
    )
