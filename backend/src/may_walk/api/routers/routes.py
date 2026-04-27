"""Ендпоинты маршрутов."""

import json
from html import escape
from typing import Annotated, Any
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

    if export_format == RouteExportFormat.geojson:
        return _geojson_export_response(route_with_geometry.route, route_with_geometry.geometry)
    if export_format == RouteExportFormat.gpx:
        return _gpx_export_response(route_with_geometry.route, route_with_geometry.geometry)

    return _kml_export_response(route_with_geometry.route, route_with_geometry.geometry)


def _route_response(route: Route, geometry: GeoJSONGeometry | None) -> RouteResponse:
    """Собрать API-ответ маршрута."""
    return RouteResponse(
        id=route.id,
        name=route.name,
        geometry=geometry,
        created_at=route.created_at,
        updated_at=route.updated_at,
    )


def _geojson_export_response(route: Route, geometry: GeoJSONGeometry) -> Response:
    """Сформировать GeoJSON-файл маршрута."""
    content = json.dumps(
        {
            'type': 'Feature',
            'properties': {'id': str(route.id), 'name': route.name},
            'geometry': geometry.model_dump(),
        },
        ensure_ascii=False,
    )
    return Response(
        content=content,
        media_type='application/geo+json',
        headers={'Content-Disposition': _attachment_header(route, 'geojson')},
    )


def _gpx_export_response(route: Route, geometry: GeoJSONGeometry) -> Response:
    """Сформировать GPX-файл маршрута."""
    segments = []
    for line in _multi_line_coordinates(geometry):
        points = ''.join(
            f'<trkpt lat="{lat}" lon="{lon}"></trkpt>' for lon, lat in line
        )
        segments.append(f'<trkseg>{points}</trkseg>')

    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<gpx version="1.1" creator="May Walk" '
        'xmlns="http://www.topografix.com/GPX/1/1">'
        f'<trk><name>{escape(route.name)}</name>{"".join(segments)}</trk>'
        '</gpx>'
    )
    return Response(
        content=content,
        media_type='application/gpx+xml',
        headers={'Content-Disposition': _attachment_header(route, 'gpx')},
    )


def _kml_export_response(route: Route, geometry: GeoJSONGeometry) -> Response:
    """Сформировать KML-файл маршрута."""
    line_strings = []
    for line in _multi_line_coordinates(geometry):
        coordinates = ' '.join(f'{lon},{lat},0' for lon, lat in line)
        line_strings.append(f'<LineString><coordinates>{coordinates}</coordinates></LineString>')

    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2">'
        '<Document>'
        f'<Placemark><name>{escape(route.name)}</name>'
        f'<MultiGeometry>{"".join(line_strings)}</MultiGeometry>'
        '</Placemark>'
        '</Document>'
        '</kml>'
    )
    return Response(
        content=content,
        media_type='application/vnd.google-earth.kml+xml',
        headers={'Content-Disposition': _attachment_header(route, 'kml')},
    )


def _multi_line_coordinates(geometry: GeoJSONGeometry) -> list[Any]:
    """Вернуть координаты MultiLineString."""
    return geometry.model_dump()['coordinates']


def _attachment_header(route: Route, extension: str) -> str:
    """Сформировать Content-Disposition для экспорта."""
    return f'attachment; filename="route-{route.id}.{extension}"'
