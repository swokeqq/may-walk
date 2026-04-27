"""Тесты endpoint'ов импорта маршрутов."""

import json

from fastapi.testclient import TestClient


def test_route_import_requires_auth(client: TestClient) -> None:
    """Проверить защиту endpoint'а импорта."""
    response = client.post('/api/routes/import')

    assert response.status_code == 401


def test_route_import_geojson(
    authenticated_client: TestClient,
    line_string_geometry: dict[str, object],
) -> None:
    """Проверить импорт маршрута из GeoJSON."""
    payload = {
        'type': 'Feature',
        'properties': {},
        'geometry': line_string_geometry,
    }

    response = authenticated_client.post(
        '/api/routes/import',
        data={'name': 'Imported GeoJSON', 'snap': 'false'},
        files={'file': ('route.geojson', json.dumps(payload), 'application/geo+json')},
    )

    assert response.status_code == 201
    assert response.json()['name'] == 'Imported GeoJSON'
    assert response.json()['geometry']['type'] == 'MultiLineString'
    assert 'total_length_m' not in response.json()


def test_route_import_gpx(authenticated_client: TestClient) -> None:
    """Проверить импорт маршрута из GPX."""
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">'
        '<trk><trkseg>'
        '<trkpt lat="56.83" lon="60.6"></trkpt>'
        '<trkpt lat="56.834" lon="60.61"></trkpt>'
        '</trkseg></trk>'
        '</gpx>'
    )

    response = authenticated_client.post(
        '/api/routes/import',
        files={'file': ('walk.gpx', content, 'application/gpx+xml')},
    )

    assert response.status_code == 201
    assert response.json()['name'] == 'walk'
    assert response.json()['geometry']['coordinates'] == [
        [[60.6, 56.83], [60.61, 56.834]],
    ]


def test_route_import_kml(authenticated_client: TestClient) -> None:
    """Проверить импорт маршрута из KML."""
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2">'
        '<Document><Placemark><LineString>'
        '<coordinates>60.6,56.83,0 60.61,56.834,0</coordinates>'
        '</LineString></Placemark></Document>'
        '</kml>'
    )

    response = authenticated_client.post(
        '/api/routes/import',
        files={'file': ('walk.kml', content, 'application/vnd.google-earth.kml+xml')},
    )

    assert response.status_code == 201
    assert response.json()['name'] == 'walk'
    assert response.json()['geometry']['coordinates'] == [
        [[60.6, 56.83], [60.61, 56.834]],
    ]


def test_route_import_with_snap_returns_error(
    authenticated_client: TestClient,
    line_string_geometry: dict[str, object],
) -> None:
    """Проверить явный отказ от импорта со snap на текущем этапе."""
    response = authenticated_client.post(
        '/api/routes/import',
        data={'snap': 'true'},
        files={'file': ('route.geojson', json.dumps(line_string_geometry))},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Route import with snap is not supported yet'
