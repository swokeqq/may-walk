"""Ендпоинты экспорта маршрутов."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db, require_auth
from may_walk.models.route import Route
from may_walk.schemas.routes import RouteExportFormat
from may_walk.services.route.crud import get_route_with_geometry
from may_walk.services.route.exports import export_route_file

router = APIRouter(
    prefix='/api/routes',
    tags=['route-export'],
    dependencies=[Depends(require_auth)],
)


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


def _attachment_header(route: Route, extension: str) -> str:
    """Сформировать Content-Disposition для экспорта."""
    return f'attachment; filename="route-{route.id}.{extension}"'
