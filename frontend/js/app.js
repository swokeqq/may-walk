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
});

undoBtn.addEventListener("click", () => {
  alert("Отмена действия пока не реализована.");
});

redoBtn.addEventListener("click", () => {
  alert("Повтор действия пока не реализован.");
});

importBtn.addEventListener("click", () => {
  alert("Импорт GPX/KML/KMZ пока не реализован.");
});

exportBtn.addEventListener("click", () => {
  alert("Экспорт GPX/KML/KMZ пока не реализован.");
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

let currentRouteId = null;
let currentRoute = null;
let isRouteChanged = false;
let visibleRouteIds = new Set();

function getEditingRouteId() {
  return currentRouteId || DRAFT_ROUTE_ID;
}

function showRoutesMessage(message, isError = false) {
  routesMessage.textContent = message;
  routesMessage.classList.toggle("error", isError);
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
  clearRouteFromMap(routeId);
  visibleRouteIds.delete(String(routeId));

  if (currentRouteId === String(routeId)) {
    setCurrentRoute(null);
  }

  renderActiveRoute();
  showRoutesMessage("Маршрут скрыт с карты.");
}

async function openRoute(routeId) {
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
  clearRouteFromMap(DRAFT_ROUTE_ID);
  setCurrentRoute(null);
  routeNameInput.value = "";
  resetRouteStats();

  showRoutesMessage("Нарисуйте новый маршрут и нажмите “Сохранить”.");
});

saveRouteBtn.addEventListener("click", async () => {
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
    let savedRoute;

    if (currentRouteId) {
      savedRoute = await updateRoute(currentRouteId, {
        name,
        geometry,
      });

      drawRouteGeometry(savedRoute.geometry || geometry, savedRoute.id);
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
  }
});

deleteRouteBtn.addEventListener("click", async () => {
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
    await deleteRoute(routeIdToDelete);

    clearRouteFromMap(routeIdToDelete);
    visibleRouteIds.delete(String(routeIdToDelete));
    setCurrentRoute(null);
    resetRouteStats();
    await loadRoutes();

    showRoutesMessage("Маршрут удалён.");
  } catch (error) {
    showRoutesMessage(error.message, true);
  }
});

loadRoutes();
resetRouteStats();