"""Ендпоинты статистики маршрутов."""

from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db, require_auth
from may_walk.api.responses import ROUTE_NOT_FOUND_RESPONSE, protected_responses
from may_walk.schemas.route.stats import RouteStatsResponse
from may_walk.services.route.crud import get_route
from may_walk.services.route.stats import calculate_route_stats

router = APIRouter(
    prefix='/api/routes',
    tags=['routes-osm'],
    dependencies=[Depends(require_auth)],
)


@router.get(
    '/{route_id:uuid}/stats',
    response_model=RouteStatsResponse,
    responses=protected_responses(
        {
            status.HTTP_400_BAD_REQUEST: {
                'description': (
                    'Маршрут существует, но у него нет геометрии для расчета '
                    'статистики.'
                ),
                'content': {
                    'application/json': {
                        'example': {'detail': {'error': 'Route has no geometry'}}
                    }
                },
            },
            status.HTTP_404_NOT_FOUND: ROUTE_NOT_FOUND_RESPONSE,
        }
    ),
)
def routes_stats(
    route_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> RouteStatsResponse:
    """Вернуть статистику маршрута по классам покрытия.

    Статистика считается динамически по пересечению `route.geometry` с
    `reference_segment.geometry`.

    Если маршрут существует, но `geometry` не задана, возвращается `400`.
    Если маршрут с `route_id` не найден, возвращается `404`.
    """
    route = get_route(db, route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Route not found',
        )
    if route.geometry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'error': 'Route has no geometry'},
        )

    return RouteStatsResponse.model_validate(
        asdict(calculate_route_stats(db, route_id))
    )
