const dateTime = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const shortDateTime = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

export const formatDateTime = (value) => (value ? dateTime.format(new Date(value)).replace(",", "") : "—");
export const formatShortDateTime = (value) => (value ? shortDateTime.format(new Date(value)).replace(",", "") : "—");

export const formatKm = (meters) => (Number(meters || 0) / 1000).toFixed(1);

export const formatCoord = ([lon, lat]) => `${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E`;

export const pluralize = (n, [one, few, many]) => {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
};

export const SURFACES = [
  { key: "asphalt_m", label: "Асфальт", color: "var(--surface-asphalt)" },
  { key: "forest_path_m", label: "Лесные тропы", color: "var(--surface-forest)" },
  { key: "field_path_m", label: "Полевые тропы", color: "var(--surface-field)" },
  { key: "rail_m", label: "Железные дороги", color: "var(--surface-rail)" },
  { key: "other_m", label: "Прочие", color: "var(--surface-other)" },
];

/** Цвета линий неактивных маршрутов на карте (активный всегда акцентный). */
export const ROUTE_PALETTE = ["#8b5cf6", "#d0a23a", "#3b82f6", "#55554f", "#c2412d", "#0e9488", "#be185d"];

export const TOOL_LABELS = { hand: "рука", brush: "кисть", eraser: "ластик" };
