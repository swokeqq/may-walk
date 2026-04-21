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