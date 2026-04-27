"""Тесты endpoint'ов экспорта маршрутов."""

from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.route.conftest import create_route


def test_route_export_requires_auth(client: TestClient) -> None:
    """Проверить защиту endpoint'а экспорта."""
    route_id = uuid4()

    response = client.get(f'/api/routes/{route_id}/export?format=geojson')

    assert response.status_code == 401


def test_route_export_formats(authenticated_client: TestClient) -> None:
    """Проверить экспорт маршрута в GeoJSON, GPX и KML."""
    route_id = create_route(authenticated_client)

    geojson_response = authenticated_client.get(
        f'/api/routes/{route_id}/export?format=geojson',
    )
    gpx_response = authenticated_client.get(f'/api/routes/{route_id}/export?format=gpx')
    kml_response = authenticated_client.get(f'/api/routes/{route_id}/export?format=kml')

    assert geojson_response.status_code == 200
    assert geojson_response.headers['content-type'].startswith('application/geo+json')
    assert geojson_response.json()['type'] == 'Feature'
    assert 'attachment; filename=' in geojson_response.headers['content-disposition']

    assert gpx_response.status_code == 200
    assert '<gpx version="1.1"' in gpx_response.text
    assert '<trkpt lat="56.83" lon="60.6"></trkpt>' in gpx_response.text

    assert kml_response.status_code == 200
    assert '<kml xmlns="http://www.opengis.net/kml/2.2">' in kml_response.text
    assert '<coordinates>60.6,56.83,0 60.61,56.834,0</coordinates>' in kml_response.text


def test_route_export_without_geometry_returns_error(
    authenticated_client: TestClient,
) -> None:
    """Проверить экспорт маршрута без геометрии."""
    response = authenticated_client.post('/api/routes', json={'name': 'Empty route'})
    route_id = response.json()['id']

    export_response = authenticated_client.get(
        f'/api/routes/{route_id}/export?format=geojson',
    )

    assert export_response.status_code == 400
    assert export_response.json()['detail'] == {'error': 'Route has no geometry'}
