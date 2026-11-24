// Состояние и бизнес-логика редактора маршрутов (порт старого app.js на React).
import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { api } from "../api/client";
import { DRAFT_ROUTE_ID } from "../map/MapEngine";
import { ROUTE_PALETTE } from "../utils/format";

const MAX_HISTORY = 50;
const SNAP_CHUNK_SIZE = 10;
const SNAP_CONTEXT_SEGMENTS = 2;

const readAutoSnap = () => {
  try {
    return localStorage.getItem("mw.autoSnap") === "true";
  } catch {
    return false;
  }
};

export function useRouteEditor({ notify, confirm }) {
  const engineRef = useRef(null);
  const handlersRef = useRef({});
  const viewListeners = useRef(new Set());

  const [auth, setAuth] = useState("unknown"); // unknown | guest | admin
  const [routes, setRoutes] = useState([]);
  const [routesLoading, setRoutesLoading] = useState(false);

  const currentRef = useRef(null);
  const [currentRoute, setCurrentRouteState] = useState(null);
  const [name, setName] = useState("");
  const dirtyRef = useRef(false);
  const [isDirty, setIsDirty] = useState(false);

  const visibleRef = useRef(new Set());
  const [visibleIds, setVisibleIdsState] = useState(() => new Set());
  const [selectedIds, setSelectedIds] = useState([]);

  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const [tool, setToolState] = useState("hand");
  const [baseLayer, setBaseLayerState] = useState("osm");
  const autoSnapRef = useRef(readAutoSnap());
  const [autoSnap, setAutoSnapState] = useState(autoSnapRef.current);

  const [busy, setBusy] = useState({});
  const [geometryVersion, bumpGeometry] = useReducer((x) => x + 1, 0);

  const undoStack = useRef([]);
  const redoStack = useRef([]);
  const [historySize, setHistorySize] = useState({ undo: 0, redo: 0 });
  const applyingHistory = useRef(false);

  const snapping = useRef(false);
  const snapQueue = useRef([]);

  const engine = () => engineRef.current;
  const editingId = () => (currentRef.current ? String(currentRef.current.id) : DRAFT_ROUTE_ID);
  const setBusyKey = (key, value) => setBusy((state) => ({ ...state, [key]: value }));

  const setVisible = (update) => {
    const next = update(new Set(visibleRef.current));
    visibleRef.current = next;
    setVisibleIdsState(next);
  };

  const markDirty = () => {
    dirtyRef.current = true;
    setIsDirty(true);
  };

  const handleError = (error, prefix) => {
    if (error?.status === 401) {
      setAuth("guest");
      notify("Сессия истекла — войдите снова", "error");
      return;
    }
    notify(prefix ? `${prefix}: ${error.message}` : error.message, "error");
  };

  // ───────────── История (undo / redo) ─────────────

  const updateHistory = () => setHistorySize({ undo: undoStack.current.length, redo: redoStack.current.length });

  const clearHistory = () => {
    undoStack.current = [];
    redoStack.current = [];
    updateHistory();
  };

  const snapshot = () => ({ routeId: editingId(), geometry: engine().routeGeometry(editingId()) });

  const pushUndo = () => {
    if (applyingHistory.current || !engine()) return;
    undoStack.current.push(snapshot());
    if (undoStack.current.length > MAX_HISTORY) undoStack.current.shift();
    redoStack.current = [];
    updateHistory();
  };

  const restore = (state) => {
    applyingHistory.current = true;
    engine().clearRoute(state.routeId);
    if (state.geometry) engine().addGeometry(state.geometry, state.routeId);
    applyingHistory.current = false;
    bumpGeometry();
  };

  const undo = () => {
    if (!undoStack.current.length) return;
    redoStack.current.push(snapshot());
    restore(undoStack.current.pop());
    markDirty();
    updateHistory();
    notify("Действие отменено");
  };

  const redo = () => {
    if (!redoStack.current.length) return;
    undoStack.current.push(snapshot());
    restore(redoStack.current.pop());
    markDirty();
    updateHistory();
    notify("Действие повторено");
  };

  // ───────────── Текущий маршрут ─────────────

  const setCurrent = (route) => {
    currentRef.current = route;
    setCurrentRouteState(route);
    setName(route?.name || "");
    dirtyRef.current = false;
    setIsDirty(false);
    clearHistory();
    engine()?.setActiveRoute(route ? String(route.id) : DRAFT_ROUTE_ID);
    bumpGeometry();
  };

  const confirmDiscard = async () => {
    if (!dirtyRef.current) return true;
    return confirm({
      title: "Несохранённые изменения",
      message: "В текущем маршруте есть несохранённые изменения. Продолжить без сохранения?",
      confirmLabel: "Не сохранять",
      danger: true,
    });
  };

  /** Убирает с карты несохранённые правки текущего маршрута (после подтверждения). */
  const discardEdits = () => {
    if (!dirtyRef.current) return;
    const id = editingId();
    engine().clearRoute(id);
    if (id !== DRAFT_ROUTE_ID) setVisible((set) => (set.delete(id), set));
  };

  const loadStats = async (id) => {
    if (!id) {
      setStats(null);
      return;
    }
    setStatsLoading(true);
    try {
      setStats(await api.routeStats(id));
    } catch (error) {
      setStats(null);
      handleError(error, "Не удалось загрузить статистику");
    } finally {
      setStatsLoading(false);
    }
  };

  const loadRoutes = async () => {
    setRoutesLoading(true);
    try {
      const result = await api.listRoutes();
      setRoutes(result.items || []);
    } catch (error) {
      handleError(error, "Не удалось загрузить маршруты");
    } finally {
      setRoutesLoading(false);
    }
  };

  // ───────────── Авторизация ─────────────

  useEffect(() => {
    (async () => {
      try {
        const result = await api.authStatus();
        if (result?.authenticated) {
          setAuth("admin");
          await loadRoutes();
        } else {
          setAuth("guest");
        }
      } catch (error) {
        setAuth("guest");
        notify(error.message, "error", { toast: error.status === 0 });
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (password) => {
    let result;
    try {
      result = await api.login(password);
    } catch (error) {
      if (error.status === 401 || error.status === 403) throw new Error("Неверный пароль");
      throw error;
    }
    if (!result?.authenticated) throw new Error("Неверный пароль");
    setAuth("admin");
    notify("Вход выполнен", "success");
    await loadRoutes();
  };

  const logout = async () => {
    if (!(await confirmDiscard())) return;
    try {
      await api.logout();
    } catch (error) {
      handleError(error);
      return;
    }
    engine()?.clearRoute(null);
    setRoutes([]);
    setVisible(() => new Set());
    setSelectedIds([]);
    setCurrent(null);
    setStats(null);
    setAuth("guest");
    notify("Вы вышли из системы");
  };

  // ───────────── Список маршрутов ─────────────

  const openRoute = async (routeId, { skipCheck = false } = {}) => {
    const id = String(routeId);
    if (editingId() === id && !skipCheck) return;
    if (!skipCheck && !(await confirmDiscard())) return;
    if (!skipCheck) discardEdits();

    notify("Загрузка маршрута…");
    try {
      const route = await api.getRoute(id);
      engine().clearRoute(DRAFT_ROUTE_ID);
      engine().drawRoute(route.geometry, id);
      setVisible((set) => set.add(id));
      setCurrent(route);
      notify(`Маршрут «${route.name}» открыт для редактирования`);
      loadStats(id);
    } catch (error) {
      handleError(error, "Не удалось открыть маршрут");
    }
  };

  const toggleVisible = async (routeId) => {
    const id = String(routeId);

    if (visibleRef.current.has(id)) {
      if (editingId() === id && !(await confirmDiscard())) return;
      engine().clearRoute(id);
      setVisible((set) => (set.delete(id), set));
      if (editingId() === id) {
        setCurrent(null);
        setStats(null);
      }
      notify("Маршрут скрыт с карты");
      return;
    }

    try {
      const route = await api.getRoute(id);
      engine().drawRoute(route.geometry, id);
      setVisible((set) => set.add(id));
      notify(`Маршрут «${route.name}» показан на карте`);
    } catch (error) {
      handleError(error, "Не удалось показать маршрут");
    }
  };

  const toggleSelected = (routeId) => {
    const id = String(routeId);
    setSelectedIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]));
  };

  const clearSelection = () => setSelectedIds([]);

  // ───────────── Инструменты карты ─────────────

  const changeTool = (nextTool) => {
    setToolState(nextTool);
    engine()?.setTool(nextTool);
  };

  const changeBaseLayer = (key) => {
    setBaseLayerState(key);
    engine()?.setBaseLayer(key);
  };

  const changeAutoSnap = (value) => {
    autoSnapRef.current = value;
    setAutoSnapState(value);
    try {
      localStorage.setItem("mw.autoSnap", String(value));
    } catch {
      /* localStorage недоступен — настройка просто не запомнится */
    }
    notify(value ? "Авто-примагничивание включено: новые линии выравниваются по дорогам" : "Авто-примагничивание выключено");
  };

  // ───────────── Примагничивание (OSRM) ─────────────

  const snapFeatures = async (routeId, features, onProgress) => {
    for (let i = 0; i < features.length; i += SNAP_CHUNK_SIZE) {
      const chunk = features.slice(i, i + SNAP_CHUNK_SIZE).filter((feature) => engine().source.hasFeature(feature));
      const geometry = engine().geometryFromFeatures(chunk);
      if (!geometry) continue;
      onProgress?.(Math.min(i + SNAP_CHUNK_SIZE, features.length), features.length);
      const result = await api.snap(geometry);
      if (!result?.snapped_geometry) throw new Error("Backend не вернул примагниченную геометрию");
      engine().replaceFeatures(routeId, chunk, result.snapped_geometry);
    }
    bumpGeometry();
  };

  const snapWholeRoute = async () => {
    const routeId = editingId();
    const features = engine().routeFeatures(routeId);
    if (!features.length) {
      notify("Сначала откройте или нарисуйте маршрут", "error");
      return;
    }
    pushUndo();
    setBusyKey("snap", true);
    try {
      await snapFeatures(routeId, features, (done, total) => notify(`Примагничивание: ${done} из ${total} сегментов…`));
      markDirty();
      notify("Маршрут примагничен — сохраните изменения", "success");
    } catch (error) {
      handleError(error, "Не удалось примагнитить маршрут");
    } finally {
      setBusyKey("snap", false);
    }
  };

  const autoSnapAfterDraw = async (newFeatures) => {
    if (!autoSnapRef.current) return;
    if (snapping.current) {
      snapQueue.current.push(...newFeatures);
      return;
    }

    snapping.current = true;
    setBusyKey("snap", true);
    let batch = newFeatures;

    try {
      while (batch.length) {
        const routeId = editingId();
        const all = engine().routeFeatures(routeId);
        const firstIndex = all.indexOf(batch[0]);
        const context = firstIndex > 0 ? all.slice(Math.max(0, firstIndex - SNAP_CONTEXT_SEGMENTS), firstIndex) : [];
        await snapFeatures(routeId, [...context, ...batch]);
        batch = snapQueue.current.splice(0);
      }
      notify("Участок примагничен — сохраните изменения", "success", { toast: false });
    } catch (error) {
      snapQueue.current = [];
      handleError(error, "Не удалось примагнитить участок");
    } finally {
      snapping.current = false;
      setBusyKey("snap", false);
    }
  };

  // ───────────── Колбэки карты ─────────────

  handlersRef.current = {
    onBeforeEdit: pushUndo,
    onEdited: (kind, features) => {
      markDirty();
      bumpGeometry();
      if (kind === "draw") {
        notify(`Добавлено сегментов: ${features.length}`);
        autoSnapAfterDraw(features);
      }
      if (kind === "erase") notify("Сегмент удалён");
    },
    onPointer: (lonLat) => viewListeners.current.forEach((listener) => listener({ pointer: lonLat })),
    onZoom: (zoom) => viewListeners.current.forEach((listener) => listener({ zoom })),
  };

  const subscribeView = useCallback((listener) => {
    viewListeners.current.add(listener);
    return () => viewListeners.current.delete(listener);
  }, []);

  // ───────────── CRUD ─────────────

  const changeName = (value) => {
    setName(value);
    if (value !== (currentRef.current?.name || "")) markDirty();
  };

  const newRoute = async () => {
    if (!(await confirmDiscard())) return;
    discardEdits();
    engine().clearRoute(DRAFT_ROUTE_ID);
    setCurrent(null);
    setStats(null);
    changeTool("brush");
    notify("Нарисуйте новый маршрут на карте, введите название и нажмите «Сохранить»");
  };

  const save = async () => {
    const trimmed = name.trim();
    const routeId = editingId();
    const geometry = engine().routeGeometry(routeId);

    if (!trimmed) {
      notify("Введите название маршрута", "error");
      return;
    }
    if (!geometry) {
      notify("Нарисуйте маршрут на карте", "error");
      return;
    }

    setBusyKey("save", true);
    try {
      let saved;
      if (currentRef.current) {
        saved = await api.updateRoute(routeId, { name: trimmed, geometry });
        engine().drawRoute(saved.geometry || geometry, String(saved.id), { fit: false });
      } else {
        saved = await api.createRoute({ name: trimmed, geometry });
        engine().changeRouteId(DRAFT_ROUTE_ID, String(saved.id));
      }
      setVisible((set) => set.add(String(saved.id)));
      setCurrent(saved);
      notify(`Маршрут «${saved.name}» сохранён`, "success");
      loadStats(String(saved.id));
      loadRoutes();
    } catch (error) {
      handleError(error, "Не удалось сохранить");
    } finally {
      setBusyKey("save", false);
    }
  };

  const deleteCurrent = async () => {
    const route = currentRef.current;
    if (!route) return;
    const ok = await confirm({
      title: "Удалить маршрут?",
      message: `«${route.name}» будет удалён без возможности восстановления.`,
      confirmLabel: "Удалить",
      danger: true,
    });
    if (!ok) return;

    const id = String(route.id);
    setBusyKey("delete", true);
    try {
      await api.deleteRoute(id);
      engine().clearRoute(id);
      setVisible((set) => (set.delete(id), set));
      setSelectedIds((ids) => ids.filter((x) => x !== id));
      setCurrent(null);
      setStats(null);
      notify("Маршрут удалён", "success");
      loadRoutes();
    } catch (error) {
      handleError(error, "Не удалось удалить");
    } finally {
      setBusyKey("delete", false);
    }
  };

  const merge = async () => {
    const ids = [...selectedIds];
    if (ids.length < 2) {
      notify("Для объединения выберите минимум два маршрута", "error");
      return;
    }
    if (!(await confirmDiscard())) return;
    discardEdits();

    setBusyKey("merge", true);
    try {
      const result = await api.merge(ids);
      if (!result?.merged_geometry) throw new Error("Backend не вернул объединённую геометрию");
      engine().clearRoute(DRAFT_ROUTE_ID);
      setCurrent(null);
      engine().addGeometry(result.merged_geometry, DRAFT_ROUTE_ID);
      engine().fit(DRAFT_ROUTE_ID);
      setName("Объединённый маршрут");
      markDirty();
      setSelectedIds([]);
      setStats(null);
      notify("Маршруты объединены — проверьте название и сохраните новый маршрут", "success");
    } catch (error) {
      handleError(error, "Не удалось объединить");
    } finally {
      setBusyKey("merge", false);
    }
  };

  // ───────────── Импорт / экспорт ─────────────

  const importFile = async (file, { name: routeName, snap }) => {
    setBusyKey("import", true);
    try {
      const route = await api.importRoute(file, { snap, name: routeName });
      notify(`Маршрут «${route.name}» импортирован`, "success");
      await loadRoutes();
      if (route?.id) {
        discardEdits();
        dirtyRef.current = false;
        await openRoute(route.id, { skipCheck: true });
      }
      return true;
    } catch (error) {
      handleError(error, "Ошибка импорта");
      return false;
    } finally {
      setBusyKey("import", false);
    }
  };

  const exportCurrent = async (format) => {
    const route = currentRef.current;
    if (!route) return false;
    setBusyKey("export", true);
    try {
      const blob = await api.exportRoute(route.id, format);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${route.name}.${format}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      notify("Файл экспорта скачан", "success");
      return true;
    } catch (error) {
      handleError(error, "Ошибка экспорта");
      return false;
    } finally {
      setBusyKey("export", false);
    }
  };

  // ───────────── Производные данные ─────────────

  const routeColors = useMemo(
    () => Object.fromEntries(routes.map((route, index) => [String(route.id), ROUTE_PALETTE[index % ROUTE_PALETTE.length]])),
    [routes],
  );

  useEffect(() => {
    engineRef.current?.setRouteColors(routeColors);
  }, [routeColors]);

  // Предупреждение браузера при закрытии вкладки с несохранёнными изменениями
  useEffect(() => {
    if (!isDirty) return undefined;
    const onBeforeUnload = (event) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [isDirty]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const segmentCount = useMemo(() => engineRef.current?.routeFeatures(editingId()).length ?? 0, [geometryVersion, currentRoute]);

  const attachEngine = useCallback((instance) => {
    engineRef.current = instance;
    if (instance) {
      instance.setTool(tool);
      instance.setBaseLayer(baseLayer);
      instance.setActiveRoute(currentRef.current ? String(currentRef.current.id) : DRAFT_ROUTE_ID);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    engineRef,
    handlersRef,
    attachEngine,
    subscribeView,
    auth,
    routes,
    routesLoading,
    routeColors,
    currentRoute,
    name,
    isDirty,
    visibleIds,
    selectedIds,
    stats,
    statsLoading,
    tool,
    baseLayer,
    autoSnap,
    busy,
    segmentCount,
    canUndo: historySize.undo > 0,
    canRedo: historySize.redo > 0,
    actions: {
      login,
      logout,
      openRoute,
      toggleVisible,
      toggleSelected,
      clearSelection,
      changeTool,
      changeBaseLayer,
      changeAutoSnap,
      changeName,
      newRoute,
      save,
      deleteCurrent,
      merge,
      snapWholeRoute,
      undo,
      redo,
      importFile,
      exportCurrent,
      confirmDiscard,
      abortDrawing: () => engine()?.abortDrawing(),
      removeLastPoint: () => engine()?.removeLastPoint(),
      zoomIn: () => engine()?.zoomBy(1),
      zoomOut: () => engine()?.zoomBy(-1),
      recenter: () => engine()?.recenter(),
    },
  };
}
