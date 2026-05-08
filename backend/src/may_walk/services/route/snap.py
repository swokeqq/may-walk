"""Примагничивание линейных геометрий к OSM через OSRM /match."""

import logging

import httpx

from may_walk.core.settings import settings
from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.geometries import normalize_line_geometry

logger = logging.getLogger(__name__)

_CHUNK_OVERLAP = 1


def snap_geometry(geometry: GeoJSONGeometry) -> GeoJSONGeometry:
    """Прогнать каждый LineString через OSRM /match и собрать результат."""
    _validate_osrm_matching_size()
    normalized = normalize_line_geometry(geometry)
    result_lines: list[list[list[float]]] = []
    for line_coords in normalized['coordinates']:
        result_lines.extend(_snap_single_line(line_coords))
    return GeoJSONGeometry.model_validate(
        {'type': 'MultiLineString', 'coordinates': result_lines}
    )


def _snap_single_line(
    line_coords: list[list[float]],
) -> list[list[list[float]]]:
    """Отправить линию в OSRM /match, при необходимости разбив на чанки."""
    if len(line_coords) < 2:
        return [line_coords]
    if len(line_coords) <= settings.osrm_max_matching_size:
        return _osrm_match(line_coords) or [line_coords]

    # Длинный трек: разбить на чанки с перекрытием в 1 точку.
    result: list[list[list[float]]] = []
    step = settings.osrm_max_matching_size - _CHUNK_OVERLAP
    i = 0
    while i < len(line_coords):
        chunk = line_coords[i : i + settings.osrm_max_matching_size]
        if len(chunk) < 2:
            break
        matched = _osrm_match(chunk)
        if matched:
            if result:
                # Первая точка чанка — это последняя точка предыдущего; пропустить.
                first_line = matched[0][1:]
                if first_line:
                    result[-1].extend(first_line)
                result.extend(m for m in matched[1:] if m)
            else:
                result.extend(m for m in matched if m)
        else:
            result.append(chunk)
        i += step

    return result or [line_coords]


def _osrm_match(
    line_coords: list[list[float]],
) -> list[list[list[float]]]:
    """Один OSRM /match запрос; вернуть список линий или [] при ошибке."""
    coords_str = ';'.join(f'{lon},{lat}' for lon, lat in line_coords)
    radiuses_str = ';'.join(str(settings.osrm_radius_m) for _ in line_coords)
    url = (
        f'{settings.osrm_url}/match/v1/foot/{coords_str}'
        f'?geometries=geojson&overview=full&gaps=split&tidy=true'
        f'&radiuses={radiuses_str}'
    )
    try:
        r = httpx.get(url, timeout=settings.osrm_timeout_s)
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning('OSRM match request failed: %s', exc)
        return []
    if data.get('code') != 'Ok':
        return []

    try:
        return [m['geometry']['coordinates'] for m in data['matchings']]
    except (KeyError, TypeError) as exc:
        logger.warning('OSRM match response is malformed: %s', exc)
        return []


def _validate_osrm_matching_size() -> None:
    """Проверить, что настройка чанков OSRM не ломает разбиение."""
    if settings.osrm_max_matching_size <= _CHUNK_OVERLAP:
        raise ValueError('OSRM_MAX_MATCHING_SIZE must be greater than 1')
