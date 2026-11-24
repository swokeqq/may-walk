// HTTP-клиент FastAPI-бэкенда. В dev-режиме /api проксируется Vite'ом (см. vite.config.js),
// поэтому запросы same-origin и HttpOnly cookie сессии отправляются автоматически.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function extractDetail(detail) {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  return JSON.stringify(detail);
}

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        ...(isFormData || !options.body ? {} : { "Content-Type": "application/json" }),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError("Сервер недоступен. Проверьте, что backend запущен.", 0);
  }

  if (response.status === 204) return null;

  const contentType = response.headers.get("Content-Type") || "";

  if (!response.ok) {
    let message = `Ошибка запроса: ${response.status}`;
    if (contentType.includes("application/json")) {
      const data = await response.json().catch(() => null);
      message = extractDetail(data?.detail) || message;
    }
    throw new ApiError(message, response.status);
  }

  if (contentType.includes("application/json")) return response.json();
  return response.blob();
}

const json = (body) => JSON.stringify(body);

export const api = {
  login: (password) => request("/auth/login", { method: "POST", body: json({ password }) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  authStatus: () => request("/auth/status"),

  listRoutes: () => request("/routes"),
  getRoute: (id) => request(`/routes/${id}`),
  createRoute: (data) => request("/routes", { method: "POST", body: json(data) }),
  updateRoute: (id, data) => request(`/routes/${id}`, { method: "PUT", body: json(data) }),
  deleteRoute: (id) => request(`/routes/${id}`, { method: "DELETE" }),

  routeStats: (id) => request(`/routes/${id}/stats`),
  snap: (geometry) => request("/routes/snap", { method: "POST", body: json({ geometry }) }),
  merge: (routeIds) => request("/routes/merge", { method: "POST", body: json({ route_ids: routeIds }) }),

  importRoute: (file, { snap = false, name = "" } = {}) => {
    const form = new FormData();
    form.append("file", file);
    form.append("snap", String(snap));
    if (name) form.append("name", name);
    return request("/routes/import", { method: "POST", body: form });
  },
  exportRoute: (id, format) => request(`/routes/${id}/export?format=${encodeURIComponent(format)}`),
};
