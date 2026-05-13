"""Ендпоинты объединения маршрутов."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db, require_auth
from may_walk.api.responses import ROUTE_NOT_FOUND_RESPONSE, protected_responses
from may_walk.schemas.geometries import GeoJSONMultiLineStringGeometry
from may_walk.schemas.route_osm.merge import RouteMergeRequest, RouteMergeResponse
from may_walk.services.route_osm.merge import (
    RouteMergeInvalidRequestError,
    RouteMergeRouteNotFoundError,
    RouteMergeRouteWithoutGeometryError,
    merge_routes,
)

router = APIRouter(
    prefix='/api/routes',
    tags=['routes-osm'],
    dependencies=[Depends(require_auth)],
)


@router.post(
    '/merge',
    response_model=RouteMergeResponse,
    responses=protected_responses(
        {
            status.HTTP_400_BAD_REQUEST: {
                'description': (
                    'Один из маршрутов существует, но у него нет геометрии для '
                    'объединения.'
                ),
                'content': {
                    'application/json': {
                        'example': {'detail': {'error': 'Route has no geometry'}}
                    }
                },
            },
            status.HTTP_404_NOT_FOUND: ROUTE_NOT_FOUND_RESPONSE,
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                'description': 'Некорректный запрос объединения маршрутов.',
            },
        }
    ),
)
def routes_merge(
    request: RouteMergeRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RouteMergeResponse:
    """Объединить сохраненные маршруты без сохранения результата.

    Примагничивает входные маршруты через OSRM, схлопывает близкие
    дублирующиеся участки и добавляет уникальные участки в итоговый
    `MultiLineString`. Далекие компоненты не соединяются между собой.

    В ответе возвращается только `snapped_geometry` в формате `MultiLineString`.
    """
    try:
        geometry = merge_routes(db, request.route_ids)
    except RouteMergeInvalidRequestError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except RouteMergeRouteNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RouteMergeRouteWithoutGeometryError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'error': str(error)},
        ) from error

    return RouteMergeResponse(
        merged_geometry=GeoJSONMultiLineStringGeometry.model_validate(
            geometry.model_dump()
        )
    )
