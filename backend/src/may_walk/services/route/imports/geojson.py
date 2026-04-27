"""Импорт маршрутов из GeoJSON."""

import json
from typing import Any

from may_walk.schemas.geometries import GeoJSONGeometry
from may_walk.services.route.imports.geometry import validated_geometry
from may_walk.services.route.imports.types import RouteImportError


class GeoJSONImportHandler:
    """Импорт маршрута из GeoJSON."""

    extensions = frozenset({'.geojson', '.json'})

    def parse(self, content: bytes) -> GeoJSONGeometry:
        """Извлечь линейную геометрию из GeoJSON."""
        try:
            payload = json.loads(content.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RouteImportError('Invalid GeoJSON file') from error

        geometry_payload = self._extract_geojson_geometry(payload)
        return validated_geometry(geometry_payload)

    def _extract_geojson_geometry(self, payload: Any) -> dict[str, Any]:
        """Найти линейную geometry внутри GeoJSON payload."""
        if not isinstance(payload, dict):
            raise RouteImportError('Invalid GeoJSON file')

        payload_type = payload.get('type')
        if payload_type in {'LineString', 'MultiLineString'}:
            return payload
        if payload_type == 'Feature':
            geometry = payload.get('geometry')
            if not isinstance(geometry, dict):
                raise RouteImportError('GeoJSON feature has no geometry')
            return self._extract_geojson_geometry(geometry)
        if payload_type == 'FeatureCollection':
            return self._extract_feature_collection_geometry(payload)

        raise RouteImportError('GeoJSON file has no route geometry')

    def _extract_feature_collection_geometry(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Собрать MultiLineString из FeatureCollection."""
        features = payload.get('features')
        if not isinstance(features, list):
            raise RouteImportError('Invalid GeoJSON feature collection')

        lines = []
        for feature in features:
            geometry = self._extract_geojson_geometry(feature)
            if geometry['type'] == 'LineString':
                lines.append(geometry['coordinates'])
            else:
                lines.extend(geometry['coordinates'])

        if not lines:
            raise RouteImportError('GeoJSON file has no route geometry')

        return {'type': 'MultiLineString', 'coordinates': lines}
