"""Ендпоинты маршрутов."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db, require_auth
from may_walk.models.route import Route
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.schemas.routes import (
    RouteCreateRequest,
    RouteExportFormat,
    RouteListItemResponse,
    RouteListResponse,
    RouteResponse,
    RouteUpdateRequest,
)
from may_walk.services.geometries import GeometryValidationError
from may_walk.services.route_exports import export_route_file
from may_walk.services.routes import (
    create_route,
    delete_route,
    get_route,
    get_route_with_geometry,
    list_routes,
    update_route,
)

router = APIRouter(
    prefix='/api/routes',
    tags=['routes'],
    dependencies=[Depends(require_auth)],
)


@router.get('', response_model=RouteListResponse)
def routes_list(db: Annotated[Session, Depends(get_db)]) -> RouteListResponse:
    """Вернуть список маршрутов без полной геометрии."""
    return RouteListResponse(
        items=[RouteListItemResponse.model_validate(route) for route in list_routes(db)],
    )


@router.post('', response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def routes_create(
    request: RouteCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RouteResponse:
    """Создать маршрут."""
    try:
        route = create_route(db, request)
    except GeometryValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    db.commit()
    route_with_geometry = get_route_with_geometry(db, route.id)
    if route_with_geometry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')

    return _route_response(route_with_geometry.route, route_with_geometry.geometry)


@router.get('/{route_id}', response_model=RouteResponse)
def routes_get(
    route_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> RouteResponse:
    """Вернуть маршрут с полной геометрией."""
    route_with_geometry = get_route_with_geometry(db, route_id)
    if route_with_geometry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')

    return _route_response(route_with_geometry.route, route_with_geometry.geometry)


@router.patch('/{route_id}', response_model=RouteResponse)
def routes_update(
    route_id: UUID,
    request: RouteUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RouteResponse:
    """Обновить маршрут."""
    route = get_route(db, route_id)
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')

    try:
        update_route(db, route, request)
    except GeometryValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    db.commit()
    route_with_geometry = get_route_with_geometry(db, route.id)
    if route_with_geometry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')

    return _route_response(route_with_geometry.route, route_with_geometry.geometry)


@router.delete('/{route_id}', status_code=status.HTTP_204_NO_CONTENT)
def routes_delete(route_id: UUID, db: Annotated[Session, Depends(get_db)]) -> Response:
    """Удалить маршрут."""
    route = get_route(db, route_id)
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')

    delete_route(db, route)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{route_id}/export')
def routes_export(
    route_id: UUID,
    export_format: Annotated[RouteExportFormat, Query(alias='format')],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Экспортировать маршрут в файл."""
    route_with_geometry = get_route_with_geometry(db, route_id)
    if route_with_geometry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Route not found')
    if route_with_geometry.geometry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'error': 'Route has no geometry'},
        )

    exported_file = export_route_file(
        route_with_geometry.route,
        route_with_geometry.geometry,
        export_format,
    )
    return Response(
        content=exported_file.content,
        media_type=exported_file.media_type,
        headers={
            'Content-Disposition': _attachment_header(
                route_with_geometry.route,
                exported_file.extension,
            ),
        },
    )


def _route_response(route: Route, geometry: GeoJSONGeometry | None) -> RouteResponse:
    """Собрать API-ответ маршрута."""
    return RouteResponse(
        id=route.id,
        name=route.name,
        geometry=geometry,
        created_at=route.created_at,
        updated_at=route.updated_at,
    )


def _attachment_header(route: Route, extension: str) -> str:
    """Сформировать Content-Disposition для экспорта."""
    return f'attachment; filename="route-{route.id}.{extension}"'
