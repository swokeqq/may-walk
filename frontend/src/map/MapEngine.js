// Императивная обёртка над OpenLayers: слои, инструменты рисования и работа с геометрией.
// React-слой общается с картой только через этот класс.
import Collection from "ol/Collection";
import OlMap from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import OSM from "ol/source/OSM";
import XYZ from "ol/source/XYZ";
import GeoJSON from "ol/format/GeoJSON";
import Draw from "ol/interaction/Draw";
import Modify from "ol/interaction/Modify";
import Select from "ol/interaction/Select";
import Snap from "ol/interaction/Snap";
import { singleClick } from "ol/events/condition";
import { MultiPoint } from "ol/geom";
import { Circle as CircleStyle, Fill, Stroke, Style } from "ol/style";
import { fromLonLat, toLonLat } from "ol/proj";
import { createEmpty, extend, isEmpty } from "ol/extent";

export const DRAFT_ROUTE_ID = "__draft_route__";

const ACCENT = "#2f7d4f";
const FALLBACK_COLOR = "#77776f";
const DEFAULT_CENTER = [60.6057, 56.8389]; // Екатеринбург

export const BASE_LAYERS = {
  osm: {
    label: "OpenStreetMap",
    createSource: () => new OSM(),
    muted: true,
    attribution: "© OpenStreetMap",
  },
  light: {
    label: "Carto Light",
    createSource: () =>
      new XYZ({
        url: "https://{a-d}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        maxZoom: 19,
      }),
    attribution: "© OpenStreetMap · © CARTO",
  },
  topo: {
    label: "OpenTopoMap",
    createSource: () =>
      new XYZ({
        url: "https://{a-c}.tile.opentopomap.org/{z}/{x}/{y}.png",
        maxZoom: 17,
      }),
    attribution: "© OpenStreetMap · © OpenTopoMap",
  },
};

const geoJson = new GeoJSON();
const projection = { dataProjection: "EPSG:4326", featureProjection: "EPSG:3857" };

export class MapEngine {
  /**
   * @param {HTMLElement} target
   * @param {{ current: object }} handlersRef — актуальные колбэки из React:
   *   onBeforeEdit(), onEdited(kind, features), onPointer([lon, lat]), onZoom(zoom)
   */
  constructor(target, handlersRef) {
    this.handlersRef = handlersRef;
    this.order = 0;
    this.activeRouteId = DRAFT_ROUTE_ID;
    this.routeColors = new Map();
    this.tool = null;
    this.interactions = [];
    this.draw = null;
    this.editable = new Collection();
    this.styleCache = new Map();

    this.source = new VectorSource();
    this.vectorLayer = new VectorLayer({
      source: this.source,
      style: (feature) => this.styleFor(feature),
      updateWhileInteracting: true,
    });
    this.baseLayer = new TileLayer({ source: BASE_LAYERS.osm.createSource(), className: "base-layer muted" });

    this.map = new OlMap({
      target,
      layers: [this.baseLayer, this.vectorLayer],
      view: new View({ center: fromLonLat(DEFAULT_CENTER), zoom: 12 }),
      controls: [],
    });

    const view = this.map.getView();
    view.on("change:resolution", () => {
      this.styleCache.clear();
      this.vectorLayer.changed();
      this.emit("onZoom", view.getZoom());
    });
    this.map.on("pointermove", (event) => {
      if (!event.dragging) this.emit("onPointer", toLonLat(event.coordinate));
    });
  }

  emit(name, ...args) {
    const handler = this.handlersRef.current?.[name];
    if (handler) handler(...args);
  }

  destroy() {
    this.clearInteractions();
    this.map.setTarget(undefined);
  }

  // ───────────── Стили ─────────────

  lineWidth() {
    const zoom = this.map?.getView().getZoom() ?? 12;
    if (zoom <= 9) return 2;
    if (zoom <= 11) return 3;
    if (zoom <= 13) return 4;
    return 5;
  }

  colorFor(routeId) {
    if (routeId === this.activeRouteId) return ACCENT;
    return this.routeColors.get(routeId) || FALLBACK_COLOR;
  }

  styleFor(feature) {
    const routeId = feature.get("routeId");
    const color = this.colorFor(routeId);
    const active = routeId === this.activeRouteId;
    const key = `${color}|${active}`;

    if (!this.styleCache.has(key)) {
      const width = this.lineWidth();
      this.styleCache.set(key, [
        new Style({
          stroke: new Stroke({ color: "rgba(255,255,255,0.95)", width: width + 4, lineCap: "round", lineJoin: "round" }),
          zIndex: active ? 10 : 1,
        }),
        new Style({
          stroke: new Stroke({ color, width: active ? width : Math.max(2, width - 1), lineCap: "round", lineJoin: "round" }),
          zIndex: active ? 11 : 2,
        }),
      ]);
    }
    return this.styleCache.get(key);
  }

  vertexStyle() {
    return [
      new Style({
        stroke: new Stroke({ color: ACCENT, width: this.lineWidth() }),
      }),
      new Style({
        image: new CircleStyle({
          radius: 5,
          fill: new Fill({ color: "#ffffff" }),
          stroke: new Stroke({ color: ACCENT, width: 2 }),
        }),
        geometry: (feature) => {
          const geometry = feature.getGeometry();
          const coordinates = geometry.getType() === "Point" ? [geometry.getCoordinates()] : geometry.getCoordinates();
          return coordinates?.length ? new MultiPoint(coordinates) : null;
        },
      }),
    ];
  }

  drawStyle() {
    return [
      new Style({
        stroke: new Stroke({ color: ACCENT, width: 3, lineDash: [6, 6], lineCap: "round" }),
        image: new CircleStyle({
          radius: 5,
          fill: new Fill({ color: ACCENT }),
          stroke: new Stroke({ color: "#ffffff", width: 2 }),
        }),
      }),
    ];
  }

  setActiveRoute(routeId) {
    this.activeRouteId = routeId || DRAFT_ROUTE_ID;
    this.styleCache.clear();
    this.syncEditable();
    this.vectorLayer.changed();
  }

  setRouteColors(colors) {
    this.routeColors = new Map(Object.entries(colors));
    this.styleCache.clear();
    this.vectorLayer.changed();
  }

  setBaseLayer(key) {
    const config = BASE_LAYERS[key] || BASE_LAYERS.osm;
    this.baseLayer.setSource(config.createSource());
    // className слоя задаётся при создании, поэтому фильтр переключаем на canvas-контейнере
    const element = this.map.getViewport().querySelector(".base-layer");
    element?.classList.toggle("muted", Boolean(config.muted));
  }

  // ───────────── Инструменты ─────────────

  clearInteractions() {
    this.interactions.forEach((interaction) => this.map.removeInteraction(interaction));
    this.interactions = [];
    this.draw = null;
  }

  addInteraction(interaction) {
    this.map.addInteraction(interaction);
    this.interactions.push(interaction);
  }

  setTool(tool) {
    this.tool = tool;
    this.clearInteractions();

    if (tool === "hand") this.enableHand();
    if (tool === "brush") this.enableBrush();
    if (tool === "eraser") this.enableEraser();
  }

  /** Рука: панорамирование + перетаскивание вершин активного маршрута. */
  enableHand() {
    const modify = new Modify({ features: this.editable, style: () => this.vertexStyle() });
    modify.on("modifystart", () => this.emit("onBeforeEdit"));
    modify.on("modifyend", (event) => this.emit("onEdited", "modify", event.features.getArray()));
    this.addInteraction(modify);
    this.addInteraction(new Snap({ source: this.source, pixelTolerance: 8 }));
  }

  /** Кисть: клики добавляют точки, двойной клик завершает линию. Линия хранится посегментно. */
  enableBrush() {
    const draw = new Draw({ type: "LineString", style: () => this.drawStyle(), stopClick: true });
    draw.on("drawstart", () => this.emit("onBeforeEdit"));
    draw.on("drawend", (event) => {
      const coordinates = event.feature.getGeometry().getCoordinates();
      const geometry = geoJson.writeGeometryObject(event.feature.getGeometry(), projection);
      if (coordinates.length < 2) return;
      const features = this.addGeometry(geometry, this.activeRouteId);
      this.emit("onEdited", "draw", features);
    });
    this.draw = draw;
    this.addInteraction(draw);
    this.addInteraction(new Snap({ source: this.source, pixelTolerance: 10 }));
  }

  /** Ластик: клик по сегменту активного маршрута удаляет его. */
  enableEraser() {
    const select = new Select({
      condition: singleClick,
      layers: [this.vectorLayer],
      filter: (feature) => feature.get("routeId") === this.activeRouteId,
      hitTolerance: 6,
      style: null,
    });
    select.on("select", (event) => {
      if (!event.selected.length) return;
      this.emit("onBeforeEdit");
      event.selected.forEach((feature) => this.source.removeFeature(feature));
      select.getFeatures().clear();
      this.syncEditable();
      this.emit("onEdited", "erase", event.selected);
    });
    this.addInteraction(select);
  }

  abortDrawing() {
    this.draw?.abortDrawing();
  }

  removeLastPoint() {
    this.draw?.removeLastPoint();
  }

  // ───────────── Геометрия ─────────────

  syncEditable() {
    this.editable.clear();
    this.editable.extend(this.routeFeatures(this.activeRouteId));
  }

  routeFeatures(routeId = null) {
    const byOrder = (a, b) => (a.get("routeOrder") || 0) - (b.get("routeOrder") || 0);
    const all = this.source.getFeatures();
    const filtered = routeId == null ? all : all.filter((feature) => feature.get("routeId") === String(routeId));
    return filtered.sort(byOrder);
  }

  geometryFromFeatures(features) {
    const lines = [];
    features.forEach((feature) => {
      const geometry = geoJson.writeGeometryObject(feature.getGeometry(), projection);
      if (geometry.type === "LineString") lines.push(geometry.coordinates);
      if (geometry.type === "MultiLineString") lines.push(...geometry.coordinates);
    });
    return lines.length ? { type: "MultiLineString", coordinates: lines } : null;
  }

  routeGeometry(routeId) {
    return this.geometryFromFeatures(this.routeFeatures(routeId));
  }

  clearRoute(routeId = null) {
    if (routeId == null) this.source.clear();
    else this.routeFeatures(routeId).forEach((feature) => this.source.removeFeature(feature));
    this.syncEditable();
  }

  /** Добавляет геометрию на карту, разбивая линии на 2-точечные сегменты (как ожидает ластик и snap). */
  addGeometry(geometry, routeId) {
    if (!geometry) return [];
    const lines =
      geometry.type === "LineString" ? [geometry.coordinates] : geometry.type === "MultiLineString" ? geometry.coordinates : [];
    const added = [];

    lines.forEach((coordinates) => {
      for (let i = 0; i < (coordinates?.length || 0) - 1; i += 1) {
        const feature = geoJson.readFeature(
          { type: "Feature", geometry: { type: "LineString", coordinates: [coordinates[i], coordinates[i + 1]] }, properties: {} },
          projection,
        );
        this.order += 1;
        feature.set("routeId", String(routeId));
        feature.set("routeOrder", this.order);
        added.push(feature);
      }
    });

    this.source.addFeatures(added);
    this.syncEditable();
    return added;
  }

  drawRoute(geometry, routeId, { fit = true } = {}) {
    this.clearRoute(routeId);
    this.addGeometry(geometry, routeId);
    if (fit) this.fit(routeId);
  }

  replaceFeatures(routeId, features, geometry) {
    features.forEach((feature) => {
      if (this.source.hasFeature(feature)) this.source.removeFeature(feature);
    });
    return this.addGeometry(geometry, routeId);
  }

  changeRouteId(oldId, newId) {
    this.routeFeatures(oldId).forEach((feature) => feature.set("routeId", String(newId)));
    this.syncEditable();
  }

  // ───────────── Вид ─────────────

  fit(routeId = null) {
    const features = this.routeFeatures(routeId);
    if (!features.length) return;
    const extent = createEmpty();
    features.forEach((feature) => extend(extent, feature.getGeometry().getExtent()));
    if (isEmpty(extent)) return;
    this.map.getView().fit(extent, { padding: [80, 80, 80, 80], maxZoom: 16, duration: 300 });
  }

  zoomBy(delta) {
    const view = this.map.getView();
    view.animate({ zoom: (view.getZoom() ?? 12) + delta, duration: 200 });
  }

  /** Показать активный маршрут, а если его нет — все видимые маршруты или центр города. */
  recenter() {
    if (this.routeFeatures(this.activeRouteId).length) this.fit(this.activeRouteId);
    else if (this.source.getFeatures().length) this.fit(null);
    else this.map.getView().animate({ center: fromLonLat(DEFAULT_CENTER), zoom: 12, duration: 300 });
  }

  getZoom() {
    return this.map.getView().getZoom();
  }
}
