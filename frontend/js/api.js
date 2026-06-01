const API_BASE_URL = "http://localhost:8000/api";

async function requestApi(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("Content-Type") || "";

  if (!response.ok) {
    let errorMessage = `Ошибка запроса: ${response.status}`;

    if (contentType.includes("application/json")) {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    }

    throw new Error(errorMessage);
  }

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.blob();
}

async function login(password) {
  return requestApi("/auth/login", {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

async function logout() {
  return requestApi("/auth/logout", {
    method: "POST",
  });
}

async function checkAuth() {
  return requestApi("/auth/status");
}

async function getRoutes() {
  return requestApi("/routes");
}

async function getRouteById(routeId) {
  return requestApi(`/routes/${routeId}`);
}

async function createRoute(routeData) {
  return requestApi("/routes", {
    method: "POST",
    body: JSON.stringify(routeData),
  });
}

async function updateRoute(routeId, routeData) {
  return requestApi(`/routes/${routeId}`, {
    method: "PUT",
    body: JSON.stringify(routeData),
  });
}

async function deleteRoute(routeId) {
  return requestApi(`/routes/${routeId}`, {
    method: "DELETE",
  });
}

async function getRouteStats(routeId) {
  return requestApi(`/routes/${routeId}/stats`);
}

async function snapRoute(geometry) {
  return requestApi("/routes/snap", {
    method: "POST",
    body: JSON.stringify({ geometry }),
  });
}

async function importRoute(file, snap = false, name = "") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("snap", String(snap));

  if (name) {
    formData.append("name", name);
  }

  return requestApi("/routes/import", {
    method: "POST",
    body: formData,
  });
}

async function exportRoute(routeId, format = "geojson") {
  return requestApi(`/routes/${routeId}/export?format=${format}`);
}

async function mergeRoutes(routeIds) {
  return requestApi("/routes/merge", {
    method: "POST",
    body: JSON.stringify({
      route_ids: routeIds,
    }),
  });
}