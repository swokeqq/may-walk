import { useMemo, useState } from "react";
import { Eye, EyeOff, GitMerge, Loader2, Lock, Plus, Route, Search, X } from "lucide-react";
import { Button, Checkbox, IconButton, Input } from "../ui";
import { formatShortDateTime, pluralize } from "../../utils/format";

function RouteItem({ route, color, active, selected, visible, onOpen, onToggleSelected, onToggleVisible }) {
  return (
    <li className={`route-item${active ? " active" : selected ? " selected" : ""}`}>
      <Checkbox checked={selected} onChange={onToggleSelected} label={`Выбрать «${route.name}» для объединения`} />
      <span className="route-swatch" style={{ background: active ? "var(--color-accent)" : color }} aria-hidden />
      <button type="button" className="route-open" onClick={onOpen} title="Открыть для редактирования">
        <span className="route-name">{route.name}</span>
        <span className="route-meta">изм. {formatShortDateTime(route.updated_at)}</span>
      </button>
      <button
        type="button"
        className={`route-eye${visible ? " on" : ""}`}
        onClick={onToggleVisible}
        aria-label={visible ? "Скрыть с карты" : "Показать на карте"}
        title={visible ? "Скрыть с карты" : "Показать на карте"}
      >
        {visible ? <Eye size={16} strokeWidth={1.75} /> : <EyeOff size={16} strokeWidth={1.75} />}
      </button>
    </li>
  );
}

export function Sidebar({ editor, onLogin }) {
  const { auth, routes, routesLoading, routeColors, currentRoute, visibleIds, selectedIds, busy, actions } = editor;
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? routes.filter((route) => route.name.toLowerCase().includes(q)) : routes;
  }, [routes, query]);

  if (auth !== "admin") {
    return (
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title">
            <h2>Маршруты</h2>
          </div>
        </div>
        <div className="empty-state">
          <span className="empty-icon">
            <Lock size={18} strokeWidth={1.75} />
          </span>
          <strong>Нужен вход</strong>
          <p>Маршруты доступны только администратору мероприятия.</p>
          {auth === "guest" && (
            <Button variant="primary" icon={Lock} onClick={onLogin}>
              Войти
            </Button>
          )}
        </div>
      </aside>
    );
  }

  const selectedCount = selectedIds.length;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <h2>Маршруты</h2>
          <span className="count">{routes.length}</span>
          <span className="spacer" />
          <Button variant="primary" icon={Plus} onClick={actions.newRoute}>
            Новый
          </Button>
        </div>
        <Input
          icon={Search}
          type="search"
          placeholder="Поиск маршрута…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="Поиск маршрута"
        />
      </div>

      {routesLoading && !routes.length ? (
        <div className="empty-state">
          <Loader2 size={18} className="spin" />
        </div>
      ) : !routes.length ? (
        <div className="empty-state">
          <span className="empty-icon">
            <Route size={18} strokeWidth={1.75} />
          </span>
          <strong>Маршрутов пока нет</strong>
          <p>Нарисуйте первый маршрут кистью или импортируйте GPX / KML / GeoJSON.</p>
        </div>
      ) : (
        <ul className="route-list">
          {filtered.map((route) => {
            const id = String(route.id);
            return (
              <RouteItem
                key={id}
                route={route}
                color={routeColors[id]}
                active={currentRoute && String(currentRoute.id) === id}
                selected={selectedIds.includes(id)}
                visible={visibleIds.has(id)}
                onOpen={() => actions.openRoute(id)}
                onToggleSelected={() => actions.toggleSelected(id)}
                onToggleVisible={() => actions.toggleVisible(id)}
              />
            );
          })}
          {!filtered.length && <li className="empty-state hint">Ничего не найдено</li>}
        </ul>
      )}

      <div className="sidebar-footer">
        {selectedCount ? (
          <>
            <span className="selected-count">{selectedCount} выбрано</span>
            <span className="spacer" />
            <IconButton icon={X} label="Снять выбор" onClick={actions.clearSelection} />
            <Button
              variant="primary"
              icon={GitMerge}
              onClick={actions.merge}
              loading={busy.merge}
              disabled={selectedCount < 2}
              title={selectedCount < 2 ? "Выберите минимум два маршрута" : undefined}
            >
              Объединить
            </Button>
          </>
        ) : (
          <span title="Отметьте маршруты галочками, чтобы объединить их">
            {routes.length} {pluralize(routes.length, ["маршрут", "маршрута", "маршрутов"])} · {visibleIds.size} на карте
          </span>
        )}
      </div>
    </aside>
  );
}
