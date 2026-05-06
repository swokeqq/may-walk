"""Ендпоинты примагничивания линейной геометрии."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db, require_auth
from may_walk.api.responses import INVALID_ROUTE_GEOMETRY_RESPONSE, protected_responses
from may_walk.schemas.geometries import GeoJSONMultiLineStringGeometry
from may_walk.schemas.route.snap import RouteSnapRequest, RouteSnapResponse
from may_walk.services.geometries import GeometryValidationError
from may_walk.services.route.snap import snap_geometry

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
    db: Annotated[Session, Depends(get_db)],
) -> RouteSnapResponse:
    """Примагнитить переданную линию к опорной сети.

    В `geometry` можно передать одну линию `LineString` или несколько линий
    `MultiLineString`. Каждый участок входной геометрии заменяется
    соответствующей ближайшей дорогой; если
    подходящая дорога не найдена, исходный участок остается без изменений.

    В ответе возвращается только `snapped_geometry` в формате `MultiLineString`.
    """
    try:
        geometry = snap_geometry(db, request.geometry)
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
