"""Ендпоинты импорта маршрутов."""

from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db, require_auth
from may_walk.api.responses import protected_responses
from may_walk.api.routers.route.responses import route_response
from may_walk.schemas.route.crud import RouteCreateRequest, RouteResponse
from may_walk.services.geometries import GeometryValidationError
from may_walk.services.route.crud import create_route, get_route_with_geometry
from may_walk.services.route.imports import RouteImportError, parse_route_file
from may_walk.services.route.snap import snap_geometry

router = APIRouter(
    prefix='/api/routes',
    tags=['routes-files'],
    dependencies=[Depends(require_auth)],
)


@router.post(
    '/import',
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    responses=protected_responses(
        {
            status.HTTP_400_BAD_REQUEST: {
                'description': 'Некорректный import payload.',
                'content': {
                    'application/json': {
                        'example': {'detail': 'Unsupported route file format'}
                    }
                },
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                'description': 'Невалидный import payload или геометрия маршрута.',
            },
        }
    ),
)
async def routes_import(
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[
        UploadFile,
        File(
            description=(
                'Файл маршрута. Поддерживаемые расширения: `.geojson`, `.json`, '
                '`.gpx`, `.kml`.'
            )
        ),
    ],
    name: Annotated[
        str | None,
        Form(
            description=(
                'Название создаваемого маршрута. Если не задано, используется '
                'имя файла без расширения.'
            ),
            examples=['Маршрут 1'],
        ),
    ] = None,
    snap: Annotated[
        bool,
        Form(
            description=(
                'Если `true`, импортированная геометрия примагничивается к '
                'опорной сети перед сохранением. По умолчанию `false`.'
            ),
            examples=[False],
        ),
    ] = False,
) -> RouteResponse:
    """Импортировать маршрут из файла.

    Endpoint всегда создает новый маршрут. Поддерживаемые форматы файлов:
    `.geojson`, `.json`, `.gpx`, `.kml`.

    Если поле формы `name` не задано, название маршрута берется из имени
    файла без расширения. Импортированная геометрия нормализуется в
    `MultiLineString`.

    Если `snap=true`, вся импортированная геометрия перед сохранением
    примагничивается к ближайщим дорогам. Участки без найденной дороги
    сохраняются как есть.
    """
    filename = file.filename or ''
    content = await file.read()
    try:
        geometry = parse_route_file(filename, content)
        if snap:
            geometry = snap_geometry(db, geometry)
        route = create_route(
            db,
            RouteCreateRequest(
                name=name or _route_name_from_filename(filename),
                geometry=geometry,
            ),
        )
    except (RouteImportError, GeometryValidationError) as error:
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


def _route_name_from_filename(filename: str) -> str:
    """Сформировать имя маршрута из имени файла."""
    stem = PurePath(filename).stem.strip()
    return stem or 'Imported route'
