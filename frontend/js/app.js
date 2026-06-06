toolButtons.forEach((button) => {
  button.addEventListener("click", () => {
    toolButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
    setTool(button.dataset.tool);
  });
});

layerButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const selectedLayer = button.dataset.layer;

    layerButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");

    setLayer(selectedLayer);
  });
});

snapToggle.addEventListener("change", () => {
  snapStatusText.textContent = snapToggle.checked ? "Включено" : "Выключено";

  if (snapToggle.checked) {
    showRoutesMessage("Примагничивание включено. Новые линии будут выравниваться по дорогам.");
  } else {
    showRoutesMessage("Примагничивание выключено.");
  }
});

snapRouteBtn.addEventListener("click", () => {
  snapCurrentEditingRoute(true);
});

undoBtn.addEventListener("click", () => {
  undoRouteChange();
});

redoBtn.addEventListener("click", () => {
  redoRouteChange();
});

const fileInputElement = document.createElement("input");
fileInputElement.type = "file";
fileInputElement.accept = ".gpx,.kml,.geojson,.json";
fileInputElement.style.display = "none";
document.body.appendChild(fileInputElement);

importBtn.addEventListener("click", () => {
  if (isImportingRoute) {
    return;
  }

  if (!confirmDiscardUnsavedChanges()) {
    return;
  }

  fileInputElement.click();
});

fileInputElement.addEventListener("change", async (event) => {
  if (isImportingRoute) {
    return;
  }

  const file = event.target.files[0];

  if (!file) {
    return;
  }

  try {
    isImportingRoute = true;
    setButtonLoading(importBtn, true, "⏳");

    showRoutesMessage("Импортирование файла маршрута...");
    const baseName = file.name.replace(/\.[^/.]+$/, "");
    const isSnapEnabled = snapToggle.checked;

    const importedRoute = await importRoute(file, isSnapEnabled, baseName);

    showRoutesMessage("Маршрут успешно импортирован!");
    await loadRoutes();

    if (importedRoute && importedRoute.id) {
      isRouteChanged = false;
      await openRoute(importedRoute.id, true);
    }
  } catch (error) {
    showRoutesMessage(`Ошибка импорта: ${error.message}`, true);
  } finally {
    isImportingRoute = false;
    setButtonLoading(importBtn, false);
    fileInputElement.value = "";
  }
});

exportBtn.addEventListener("click", () => {
  if (isExportingRoute) {
    return;
  }

  if (!currentRouteId) {
    showRoutesMessage("Сначала выберите сохранённый маршрут для экспорта.", true);
    return;
  }

  exportModal.classList.remove("hidden");
});

closeExportModalBtn.addEventListener("click", () => {
  exportModal.classList.add("hidden");
});

confirmExportBtn.addEventListener("click", async () => {
  if (isExportingRoute) {
    return;
  }

  if (!currentRouteId) {
    showRoutesMessage("Сначала выберите сохранённый маршрут для экспорта.", true);
    exportModal.classList.add("hidden");
    return;
  }

  const selectedFormat = exportFormatSelect.value;
  exportModal.classList.add("hidden");

  try {
    isExportingRoute = true;
    setButtonLoading(confirmExportBtn, true, "Скачивание...");

    showRoutesMessage("Формирование файла экспорта...");
    const blob = await exportRoute(currentRouteId, selectedFormat);

    const downloadUrl = URL.createObjectURL(blob);
    const downloadAnchor = document.createElement("a");

    downloadAnchor.href = downloadUrl;
    downloadAnchor.download = `${currentRoute ? currentRoute.name : "route"}.${selectedFormat}`;

    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();

    document.body.removeChild(downloadAnchor);
    URL.revokeObjectURL(downloadUrl);

    showRoutesMessage("Маршрут успешно экспортирован.");
  } catch (error) {
    showRoutesMessage(`Ошибка экспорта: ${error.message}`, true);
  } finally {
    isExportingRoute = false;
    setButtonLoading(confirmExportBtn, false);
  }
});

setTool("hand");

function setAuthStatus(isAuthenticated) {
  authStatusText.textContent = isAuthenticated ? "Авторизован" : "Не авторизован";
  loginBtn.disabled = isAuthenticated;
  logoutBtn.disabled = !isAuthenticated;
}

function showAuthMessage(message, isError = false) {
  authMessage.textContent = message;
  authMessage.classList.toggle("error", isError);
}

async function updateAuthStatus() {
  try {
    const result = await checkAuth();

    setAuthStatus(result.authenticated);
    showAuthMessage(result.authenticated ? "Вход выполнен." : "Нужно войти.");
  } catch (error) {
    setAuthStatus(false);
    showAuthMessage("Нужно войти в систему.", true);
  }
}

loginBtn.addEventListener("click", async () => {
  const password = authPasswordInput.value.trim();

  if (!password) {
    showAuthMessage("Введите пароль.", true);
    return;
  }

  try {
    const result = await login(password);

    if (result.authenticated) {
      setAuthStatus(true);
      showAuthMessage("Вход выполнен успешно.");
      authPasswordInput.value = "";

      await loadRoutes();
    } else {
      setAuthStatus(false);
      showAuthMessage("Неверный пароль.", true);
    }
  } catch (error) {
    setAuthStatus(false);
    showAuthMessage(error.message, true);
  }
});

logoutBtn.addEventListener("click", async () => {
  if (!confirmDiscardUnsavedChanges()) {
    return;
  }

  try {
    await logout();
    setAuthStatus(false);
    showAuthMessage("Вы вышли из системы.");
  } catch (error) {
    showAuthMessage(error.message, true);
  }
});

authPasswordInput.addEventListener("keydown", (evt) => {
  if (evt.key === "Enter") {
    loginBtn.click();
  }
});

updateAuthStatus();

const DRAFT_ROUTE_ID = "__draft_route__";
const SNAP_CONTEXT_LINES_COUNT = 3;
const SNAP_FULL_ROUTE_CHUNK_SIZE = 10;

let currentRouteId = null;
let currentRoute = null;
let isRouteChanged = false;
let visibleRouteIds = new Set();

let isSavingRoute = false;
let isDeletingRoute = false;
let isMergingRoutes = false;
let isImportingRoute = false;
let isExportingRoute = false;

const undoStack = [];
const redoStack = [];
const MAX_HISTORY_LENGTH = 50;

let isApplyingHistory = false;

function setButtonLoading(button, isLoading, loadingText = "") {
  if (!button) {
    return;
  }

  if (isLoading) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }

    button.disabled = true;

    if (loadingText) {
      button.textContent = loadingText;
    }

    return;
  }

  button.disabled = false;

  if (button.dataset.originalText) {
    button.textContent = button.dataset.originalText;
    delete button.dataset.originalText;
  }
}

function cloneGeometry(geometry) {
  return geometry ? JSON.parse(JSON.stringify(geometry)) : null;
}

function createRouteSnapshot() {
  const routeId = getEditingRouteId();

  return {
    routeId,
    geometry: cloneGeometry(getRouteGeometryFromMap(routeId)),
  };
}

function updateUndoRedoButtons() {
  undoBtn.disabled = undoStack.length === 0;
  redoBtn.disabled = redoStack.length === 0;
}

function clearRouteHistory() {
  undoStack.length = 0;
  redoStack.length = 0;
  updateUndoRedoButtons();
}

function saveRouteStateForUndo() {
  if (isApplyingHistory) {
    return;
  }

  undoStack.push(createRouteSnapshot());

  if (undoStack.length > MAX_HISTORY_LENGTH) {
    undoStack.shift();
  }

  redoStack.length = 0;
  updateUndoRedoButtons();
}

function restoreRouteSnapshot(snapshot) {
  if (!snapshot) {
    return;
  }

  isApplyingHistory = true;

  clearRouteFromMap(snapshot.routeId);

  if (snapshot.geometry) {
    drawRouteGeometry(snapshot.geometry, snapshot.routeId, false, false);
  }

  isApplyingHistory = false;
}

function undoRouteChange() {
  if (!undoStack.length) {
    showRoutesMessage("Нет действий для отмены.", true);
    return;
  }

  const currentSnapshot = createRouteSnapshot();
  const previousSnapshot = undoStack.pop();

  redoStack.push(currentSnapshot);
  restoreRouteSnapshot(previousSnapshot);
  markRouteAsChanged();
  updateUndoRedoButtons();

  showRoutesMessage("Действие отменено. Нажмите “Сохранить”, чтобы записать изменения.");
}

function redoRouteChange() {
  if (!redoStack.length) {
    showRoutesMessage("Нет действий для повтора.", true);
    return;
  }

  const currentSnapshot = createRouteSnapshot();
  const nextSnapshot = redoStack.pop();

  undoStack.push(currentSnapshot);
  restoreRouteSnapshot(nextSnapshot);
  markRouteAsChanged();
  updateUndoRedoButtons();

  showRoutesMessage("Действие повторено. Нажмите “Сохранить”, чтобы записать изменения.");
}

function getEditingRouteId() {
  return currentRouteId || DRAFT_ROUTE_ID;
}

function showRoutesMessage(message, isError = false) {
  routesMessage.textContent = message;
  routesMessage.classList.toggle("error", isError);
}

function confirmDiscardUnsavedChanges() {
  if (!isRouteChanged) {
    return true;
  }

  return confirm("Есть несохранённые изменения. Продолжить без сохранения?");
}

let isSnappingRoute = false;
let shouldSnapRouteAgain = false;

async function snapFeatureGroup(routeId, features, shouldFit = false) {
  const geometry = getRouteGeometryFromFeatures(features);

  if (!geometry) {
    return false;
  }

  const result = await snapRoute(geometry);

  if (!result.snapped_geometry) {
    throw new Error("Backend не вернул примагниченную геометрию.");
  }

  replaceRouteFeaturesWithGeometry(routeId, features, result.snapped_geometry, shouldFit, false);

  return true;
}

async function snapLastRouteLines() {
  const editingRouteId = getEditingRouteId();
  const snapFeatures = getLastRouteFeatures(editingRouteId, SNAP_CONTEXT_LINES_COUNT);

  if (!snapFeatures.length) {
    showRoutesMessage("Сначала выберите или нарисуйте маршрут.", true);
    return;
  }

  saveRouteStateForUndo();

  showRoutesMessage(`Выполняется примагничивание последних ${snapFeatures.length} линий маршрута...`);

  await snapFeatureGroup(editingRouteId, snapFeatures, false);

  markRouteAsChanged();
  showRoutesMessage("Участок маршрута примагничен. Нажмите “Сохранить”, чтобы записать изменения.");
}

async function snapFullCurrentRoute() {
  const editingRouteId = getEditingRouteId();
  const routeFeatures = getRouteFeatures(editingRouteId);

  if (!routeFeatures.length) {
    showRoutesMessage("Сначала выберите или импортируйте маршрут.", true);
    return;
  }

  saveRouteStateForUndo();

  for (let i = 0; i < routeFeatures.length; i += SNAP_FULL_ROUTE_CHUNK_SIZE) {
    const chunk = routeFeatures.slice(i, i + SNAP_FULL_ROUTE_CHUNK_SIZE);
    const processedCount = Math.min(i + SNAP_FULL_ROUTE_CHUNK_SIZE, routeFeatures.length);

    showRoutesMessage(
      `Примагничивание маршрута: обработано ${processedCount} из ${routeFeatures.length} участков...`
    );

    await snapFeatureGroup(editingRouteId, chunk, false);
  }

  markRouteAsChanged();

  showRoutesMessage("Весь маршрут примагничен. Нажмите “Сохранить”, чтобы записать изменения.");
}

async function snapCurrentEditingRoute(force = false) {
  if (isSnappingRoute) {
    if (!force && snapToggle.checked) {
      shouldSnapRouteAgain = true;
    }

    return;
  }

  if (!force && !snapToggle.checked) {
    return;
  }

  try {
    isSnappingRoute = true;
    snapRouteBtn.disabled = true;

    if (force) {
      await snapFullCurrentRoute();
    } else {
      await snapLastRouteLines();
    }
  } catch (error) {
    showRoutesMessage(`Не удалось примагнитить маршрут: ${error.message}`, true);
  } finally {
    isSnappingRoute = false;
    snapRouteBtn.disabled = false;

    if (shouldSnapRouteAgain && snapToggle.checked) {
      shouldSnapRouteAgain = false;
      setTimeout(() => snapCurrentEditingRoute(false), 0);
    }
  }
}

function formatDistanceKm(meters) {
  return `${(Number(meters || 0) / 1000).toFixed(1)} км`;
}

function resetRouteStats() {
  asphaltDistanceText.textContent = "0.0 км";
  forestDistanceText.textContent = "0.0 км";
  fieldDistanceText.textContent = "0.0 км";
  railDistanceText.textContent = "0.0 км";
  otherDistanceText.textContent = "0.0 км";
  totalDistanceText.textContent = "0.0 км";
}

async function updateRouteStats(routeId) {
  if (!routeId) {
    resetRouteStats();
    return;
  }

  try {
    const stats = await getRouteStats(routeId);

    asphaltDistanceText.textContent = formatDistanceKm(stats.asphalt_m);
    forestDistanceText.textContent = formatDistanceKm(stats.forest_path_m);
    fieldDistanceText.textContent = formatDistanceKm(stats.field_path_m);
    railDistanceText.textContent = formatDistanceKm(stats.rail_m);
    otherDistanceText.textContent = formatDistanceKm(stats.other_m);
    totalDistanceText.textContent = formatDistanceKm(stats.total_m);
  } catch (error) {
    resetRouteStats();
    showRoutesMessage(`Не удалось загрузить статистику: ${error.message}`, true);
  }
}

function setCurrentRoute(route) {
  currentRoute = route;
  currentRouteId = route ? String(route.id) : null;
  isRouteChanged = false;

  currentRouteText.textContent = route ? route.name : "Не выбран";
  routeNameInput.value = route ? route.name : "";

  clearRouteHistory();
  renderActiveRoute();
}

function markRouteAsChanged() {
  isRouteChanged = true;

  if (currentRoute) {
    currentRouteText.textContent = `${currentRoute.name} *`;
  } else {
    currentRouteText.textContent = "Новый маршрут *";
  }
}

function renderActiveRoute() {
  const routeButtons = routesList.querySelectorAll(".route-list-btn");
  const routeCheckboxes = routesList.querySelectorAll(".route-visible-checkbox");

  routeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.routeId === currentRouteId);
  });

  routeCheckboxes.forEach((checkbox) => {
    checkbox.checked = visibleRouteIds.has(checkbox.dataset.routeId);
  });
}

function renderRoutes(routes) {
  routesList.innerHTML = "";

  if (!routes.length) {
    routesList.innerHTML = `<li class="routes-empty">Маршрутов пока нет</li>`;
    return;
  }

  routes.forEach((route) => {
    const routeId = String(route.id);

    const item = document.createElement("li");
    item.className = "route-list-item";

    const row = document.createElement("div");
    row.className = "route-list-row";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "route-visible-checkbox";
    checkbox.dataset.routeId = routeId;
    checkbox.checked = visibleRouteIds.has(routeId);
    checkbox.title = "Показать маршрут на карте";

    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        showRouteOnMap(routeId);
      } else {
        hideRouteFromMap(routeId);
      }
    });

    const button = document.createElement("button");
    button.className = "route-list-btn";
    button.dataset.routeId = routeId;
    button.textContent = route.name;
    button.title = "Открыть маршрут для редактирования";

    button.addEventListener("click", () => {
      openRoute(routeId);
    });

    row.appendChild(checkbox);
    row.appendChild(button);
    item.appendChild(row);
    routesList.appendChild(item);
  });

  renderActiveRoute();
}

async function loadRoutes() {
  try {
    const result = await getRoutes();
    renderRoutes(result.items || []);
    showRoutesMessage("Список маршрутов загружен.");
  } catch (error) {
    showRoutesMessage(error.message, true);
  }
}

async function showRouteOnMap(routeId) {
  try {
    const route = await getRouteById(routeId);

    drawRouteGeometry(route.geometry, route.id);
    visibleRouteIds.add(String(route.id));

    renderActiveRoute();
    showRoutesMessage("Маршрут показан на карте.");
  } catch (error) {
    showRoutesMessage(error.message, true);
  }
}

function hideRouteFromMap(routeId) {
  if (currentRouteId === String(routeId) && !confirmDiscardUnsavedChanges()) {
    renderActiveRoute();
    return;
  }

  clearRouteFromMap(routeId);
  visibleRouteIds.delete(String(routeId));

  if (currentRouteId === String(routeId)) {
    setCurrentRoute(null);
  }

  renderActiveRoute();
  showRoutesMessage("Маршрут скрыт с карты.");
}

async function openRoute(routeId, skipUnsavedCheck = false) {
  if (currentRouteId !== String(routeId) && !skipUnsavedCheck && !confirmDiscardUnsavedChanges()) {
    return;
  }

  try {
    const route = await getRouteById(routeId);

    drawRouteGeometry(route.geometry, route.id);
    visibleRouteIds.add(String(route.id));
    setCurrentRoute(route);
    await updateRouteStats(route.id);

    showRoutesMessage("Маршрут открыт для редактирования.");
  } catch (error) {
    showRoutesMessage(error.message, true);
  }
}

newRouteBtn.addEventListener("click", () => {
  if (!confirmDiscardUnsavedChanges()) {
    return;
  }

  clearRouteFromMap(DRAFT_ROUTE_ID);
  setCurrentRoute(null);
  routeNameInput.value = "";
  resetRouteStats();

  showRoutesMessage("Нарисуйте новый маршрут и нажмите “Сохранить”.");
});

saveRouteBtn.addEventListener("click", async () => {
  if (isSavingRoute) {
    return;
  }

  const name = routeNameInput.value.trim();
  const editingRouteId = getEditingRouteId();
  const geometry = getRouteGeometryFromMap(editingRouteId);

  if (!name) {
    showRoutesMessage("Введите название маршрута.", true);
    return;
  }

  if (!geometry) {
    showRoutesMessage("Нарисуйте маршрут на карте.", true);
    return;
  }

  try {
    isSavingRoute = true;
    setButtonLoading(saveRouteBtn, true, "Сохранение...");

    let savedRoute;

    if (currentRouteId) {
      savedRoute = await updateRoute(currentRouteId, {
        name,
        geometry,
      });

      drawRouteGeometry(savedRoute.geometry || geometry, savedRoute.id, false, false);
      visibleRouteIds.add(String(savedRoute.id));
      showRoutesMessage("Маршрут обновлён.");
    } else {
      savedRoute = await createRoute({
        name,
        geometry,
      });

      changeRouteFeaturesId(DRAFT_ROUTE_ID, savedRoute.id);
      visibleRouteIds.add(String(savedRoute.id));
      showRoutesMessage("Маршрут создан.");
    }

    setCurrentRoute(savedRoute);
    await updateRouteStats(savedRoute.id);
    await loadRoutes();
  } catch (error) {
    showRoutesMessage(error.message, true);
  } finally {
    isSavingRoute = false;
    setButtonLoading(saveRouteBtn, false);
  }
});

mergeRoutesBtn.addEventListener("click", async () => {
  if (isMergingRoutes) {
    return;
  }

  if (!confirmDiscardUnsavedChanges()) {
    return;
  }

  const routeIds = Array.from(visibleRouteIds);

  if (routeIds.length < 2) {
    showRoutesMessage("Для объединения выберите галочками минимум два маршрута.", true);
    return;
  }

  try {
    isMergingRoutes = true;
    setButtonLoading(mergeRoutesBtn, true, "Объединение...");

    showRoutesMessage("Выполняется объединение выбранных маршрутов...");

    const result = await mergeRoutes(routeIds);

    if (!result.merged_geometry) {
      showRoutesMessage("Backend не вернул объединённую геометрию.", true);
      return;
    }

    clearRouteFromMap(DRAFT_ROUTE_ID);
    drawRouteGeometry(result.merged_geometry, DRAFT_ROUTE_ID);

    setCurrentRoute(null);
    routeNameInput.value = "Объединённый маршрут";
    resetRouteStats();
    clearRouteHistory();
    markRouteAsChanged();

    showRoutesMessage(
      "Маршруты объединены на карте. Введите название и нажмите “Сохранить”, чтобы создать новый маршрут."
    );
  } catch (error) {
    showRoutesMessage(`Не удалось объединить маршруты: ${error.message}`, true);
  } finally {
    isMergingRoutes = false;
    setButtonLoading(mergeRoutesBtn, false);
  }
});

deleteRouteBtn.addEventListener("click", async () => {
  if (isDeletingRoute) {
    return;
  }

  if (!currentRouteId) {
    showRoutesMessage("Сначала выберите маршрут.", true);
    return;
  }

  const routeIdToDelete = currentRouteId;
  const confirmed = confirm("Удалить выбранный маршрут?");

  if (!confirmed) {
    return;
  }

  try {
    isDeletingRoute = true;
    setButtonLoading(deleteRouteBtn, true, "Удаление...");

    await deleteRoute(routeIdToDelete);

    clearRouteFromMap(routeIdToDelete);
    visibleRouteIds.delete(String(routeIdToDelete));
    setCurrentRoute(null);
    resetRouteStats();
    await loadRoutes();

    showRoutesMessage("Маршрут удалён.");
  } catch (error) {
    showRoutesMessage(error.message, true);
  } finally {
    isDeletingRoute = false;
    setButtonLoading(deleteRouteBtn, false);
  }
});

loadRoutes();
resetRouteStats();
updateUndoRedoButtons();
