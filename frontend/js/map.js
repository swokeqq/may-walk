let activeTool = "hand";
let activeLayer = "osm";
let drawInteraction = null;
let selectInteraction = null;
let modifyInteraction = null;

function getLineWidth() {
  const zoom = map.getView().getZoom() || 12;
  if (zoom <= 9) return 2;
  if (zoom <= 11) return 3;
  if (zoom <= 13) return 4;
  return 5;
}

function createLineStyle() {
  return new ol.style.Style({
    stroke: new ol.style.Stroke({
      color: "#d32f2f",
      width: getLineWidth(),
    }),
  });
}

function createModifyStyle() {
  return [
    new ol.style.Style({
      stroke: new ol.style.Stroke({
        color: "#d32f2f",
        width: getLineWidth(),
      }),
    }),
    new ol.style.Style({
      image: new ol.style.Circle({
        radius: 6,
        fill: new ol.style.Fill({
          color: "#ffffff",
        }),
        stroke: new ol.style.Stroke({
          color: "#d32f2f",
          width: 2,
        }),
      }),
      geometry: function (feature) {
        const coordinates = feature.getGeometry().getCoordinates();
        if (!coordinates || !coordinates.length) return null;
        return new ol.geom.MultiPoint(coordinates);
      },
    }),
  ];
}

const source = new ol.source.Vector();

const vectorLayer = new ol.layer.Vector({
  source: source,
  style: () => createLineStyle(),
});

const baseLayer = new ol.layer.Tile({
  source: new ol.source.OSM({
    attributions: "",
  }),
});

const map = new ol.Map({
  target: "map",
  layers: [baseLayer, vectorLayer],
  view: new ol.View({
    center: ol.proj.fromLonLat([60.6057, 56.8389]),
    zoom: 12,
  }),
  controls: [],
});

map.getView().on("change:resolution", () => {
  vectorLayer.changed();
});

function getRouteFeatures(routeId = null) {
  if (!routeId) {
    return source.getFeatures();
  }

  return source.getFeatures().filter((feature) => {
    return String(feature.get("routeId")) === String(routeId);
  });
}

function getLastRouteFeatures(routeId, limit = 10) {
  const features = getRouteFeatures(routeId);

  return features.slice(-limit);
}

function getRouteGeometryFromFeatures(features) {
  if (!features.length) {
    return null;
  }

  const format = new ol.format.GeoJSON();
  const lines = [];

  features.forEach((feature) => {
    const geometry = feature.getGeometry();

    const geojsonGeometry = format.writeGeometryObject(geometry, {
      featureProjection: "EPSG:3857",
      dataProjection: "EPSG:4326",
    });

    if (geojsonGeometry.type === "LineString") {
      lines.push(geojsonGeometry.coordinates);
    }

    if (geojsonGeometry.type === "MultiLineString") {
      lines.push(...geojsonGeometry.coordinates);
    }
  });

  if (!lines.length) {
    return null;
  }

  return {
    type: "MultiLineString",
    coordinates: lines,
  };
}

function getRouteGeometryFromMap(routeId = null) {
  return getRouteGeometryFromFeatures(getRouteFeatures(routeId));
}

function clearRouteFromMap(routeId = null) {
  if (!routeId) {
    source.clear();
    return;
  }

  getRouteFeatures(routeId).forEach((feature) => {
    source.removeFeature(feature);
  });
}

function addRouteGeometryToMap(geometry, routeId = null) {
  if (!geometry) {
    return;
  }

  const format = new ol.format.GeoJSON();

  function addLineFeature(lineGeometry) {
    const feature = format.readFeature(
      {
        type: "Feature",
        geometry: lineGeometry,
        properties: {},
      },
      {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }
    );

    if (routeId) {
      feature.set("routeId", String(routeId));
    }

    source.addFeature(feature);
  }

  if (geometry.type === "LineString") {
    addLineFeature(geometry);
  }

  if (geometry.type === "MultiLineString") {
    geometry.coordinates.forEach((lineCoordinates) => {
      addLineFeature({
        type: "LineString",
        coordinates: lineCoordinates,
      });
    });
  }
}

function drawRouteGeometry(geometry, routeId = null, shouldClearMap = false) {
  if (shouldClearMap) {
    clearRouteFromMap();
  }

  if (routeId) {
    clearRouteFromMap(routeId);
  }

  addRouteGeometryToMap(geometry, routeId);
  fitMapToRoute();
}

function replaceRouteFeaturesWithGeometry(routeId, featuresToReplace, geometry) {
  featuresToReplace.forEach((feature) => {
    source.removeFeature(feature);
  });

  addRouteGeometryToMap(geometry, routeId);
  fitMapToRoute();
}

function changeRouteFeaturesId(oldRouteId, newRouteId) {
  getRouteFeatures(oldRouteId).forEach((feature) => {
    feature.set("routeId", String(newRouteId));
  });
}

function fitMapToRoute() {
  const features = source.getFeatures();

  if (!features.length) {
    return;
  }

  const extent = source.getExtent();

  if (ol.extent.isEmpty(extent)) {
    return;
  }

  map.getView().fit(extent, {
    padding: [60, 60, 60, 60],
    maxZoom: 16,
    duration: 300,
  });
}