"""CRUD-ендпоинты маршрутов."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db, require_auth
from may_walk.api.responses import (
    INVALID_ROUTE_GEOMETRY_RESPONSE,
    ROUTE_NOT_FOUND_RESPONSE,
    protected_responses,
)
from may_walk.api.routers.route.responses import route_response
from may_walk.schemas.routes import (
    RouteCreateRequest,
    RouteListItemResponse,
    RouteListResponse,
    RouteResponse,
    RouteUpdateRequest,
)
from may_walk.services.geometries import GeometryValidationError
from may_walk.services.route.crud import (
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


@router.get('', response_model=RouteListResponse, responses=protected_responses())
def routes_list(db: Annotated[Session, Depends(get_db)]) -> RouteListResponse:
    """Вернуть список маршрутов без полной геометрии.

    Поле `geometry` в ответе не возвращается; для получения полной геометрии
    используйте `GET /api/routes/{route_id}`.

    Маршруты возвращаются в порядке создания.
    """
    return RouteListResponse(
        items=[
            RouteListItemResponse.model_validate(route) for route in list_routes(db)
        ],
    )


@router.post(
    '',
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    responses=protected_responses(
        {status.HTTP_422_UNPROCESSABLE_CONTENT: INVALID_ROUTE_GEOMETRY_RESPONSE}
    ),
)
def routes_create(
    request: RouteCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RouteResponse:
    """Создать новый маршрут.

    Поведение поля `geometry`:
    - если поле отсутствует, маршрут создается без геометрии;
    - если передано `geometry: null`, маршрут создается без геометрии;
    - если передана GeoJSON-геометрия, она задает всю начальную геометрию
      маршрута целиком; `LineString` нормализуется в `MultiLineString`.
    """
    try:
        route = create_route(db, request)
    except GeometryValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    db.commit()
    route_with_geometry = get_route_with_geometry(db, route.id)
    if route_with_geometry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Route not found'
        )

    return route_response(route_with_geometry.route, route_with_geometry.geometry)


@router.get(
    '/{route_id:uuid}',
    response_model=RouteResponse,
    responses=protected_responses(
        {status.HTTP_404_NOT_FOUND: ROUTE_NOT_FOUND_RESPONSE}
    ),
)
def routes_get(
    route_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> RouteResponse:
    """Вернуть маршрут с полной геометрией."""
    route_with_geometry = get_route_with_geometry(db, route_id)
    if route_with_geometry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Route not found'
        )

    return route_response(route_with_geometry.route, route_with_geometry.geometry)


@router.patch(
    '/{route_id:uuid}',
    response_model=RouteResponse,
    responses=protected_responses(
        {
            status.HTTP_404_NOT_FOUND: ROUTE_NOT_FOUND_RESPONSE,
            status.HTTP_422_UNPROCESSABLE_CONTENT: INVALID_ROUTE_GEOMETRY_RESPONSE,
        }
    ),
)
def routes_update(
    route_id: UUID,
    request: RouteUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RouteResponse:
    """Обновить маршрут.

    Поведение поля `geometry`:
    - если поле отсутствует, геометрия маршрута не меняется;
    - если передано `geometry: null`, геометрия удаляется;
    - если передана GeoJSON-геометрия, она заменяет всю геометрию маршрута
      целиком.

    Endpoint не добавляет линию инкрементально. Для добавления линии клиент
    должен отправить полный обновленный `MultiLineString`.
    """
    route = get_route(db, route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Route not found'
        )

    try:
        update_route(db, route, request)
    except GeometryValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    db.commit()
    route_with_geometry = get_route_with_geometry(db, route.id)
    if route_with_geometry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Route not found'
        )

    return route_response(route_with_geometry.route, route_with_geometry.geometry)


@router.delete(
    '/{route_id:uuid}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses=protected_responses(
        {status.HTTP_404_NOT_FOUND: ROUTE_NOT_FOUND_RESPONSE}
    ),
)
def routes_delete(route_id: UUID, db: Annotated[Session, Depends(get_db)]) -> Response:
    """Удалить маршрут."""
    route = get_route(db, route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Route not found'
        )

    delete_route(db, route)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
