"""Ендпоинты примагничивания линейной геометрии."""

from fastapi import APIRouter, Depends, HTTPException, status

from may_walk.api.dependencies import require_auth
from may_walk.api.responses import INVALID_ROUTE_GEOMETRY_RESPONSE, protected_responses
from may_walk.schemas.geometries import GeoJSONMultiLineStringGeometry
from may_walk.schemas.route_osm.snap import RouteSnapRequest, RouteSnapResponse
from may_walk.services.geometries import GeometryValidationError
from may_walk.services.route_osm.snap import snap_geometry

router = APIRouter(
    prefix='/api/routes',
    tags=['routes-osm'],
    dependencies=[Depends(require_auth)],
)


@router.post(
    '/snap',
    response_model=RouteSnapResponse,
    responses=protected_responses(
        {status.HTTP_422_UNPROCESSABLE_CONTENT: INVALID_ROUTE_GEOMETRY_RESPONSE}
    ),
)
def routes_snap(
    request: RouteSnapRequest,
) -> RouteSnapResponse:
    """Примагнитить переданную линию к OSM через OSRM.

    В `geometry` можно передать одну линию `LineString` или несколько линий
    `MultiLineString`. Каждый участок входной геометрии отправляется в OSRM;
    если подходящее совпадение не найдено или OSRM недоступен,
    исходный участок остается без изменений.

    В ответе возвращается только `snapped_geometry` в формате `MultiLineString`.
    """
    try:
        geometry = snap_geometry(request.geometry)
    except GeometryValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    return RouteSnapResponse(
        snapped_geometry=GeoJSONMultiLineStringGeometry.model_validate(
            geometry.model_dump()
        )
    )
