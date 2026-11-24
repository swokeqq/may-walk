import { Lock, Magnet, Save, Trash2 } from "lucide-react";
import { Button, Input, Toggle } from "../ui";
import { formatDateTime, formatKm, SURFACES } from "../../utils/format";

function StatsPanel({ stats, loading, hasRoute }) {
  if (!hasRoute) {
    return (
      <section className="panel">
        <span className="label">Покрытие</span>
        <p className="hint" style={{ margin: 0 }}>
          Статистика по типам покрытия появится после сохранения маршрута.
        </p>
      </section>
    );
  }

  const total = Number(stats?.total_m || 0);

  return (
    <section className={`panel${loading ? " stats-loading" : ""}`} aria-busy={loading}>
      <span className="label">Покрытие</span>
      <div className="stat-total">
        <strong>{formatKm(total)}</strong>
        <span>км всего</span>
      </div>
      <div className="stat-bar" aria-hidden>
        {SURFACES.map((surface) => {
          const value = Number(stats?.[surface.key] || 0);
          return value > 0 ? <span key={surface.key} style={{ flexGrow: value, background: surface.color }} /> : null;
        })}
      </div>
      <ul className="stat-rows">
        {SURFACES.map((surface) => {
          const value = Number(stats?.[surface.key] || 0);
          const percent = total ? Math.round((value / total) * 100) : 0;
          return (
            <li className="stat-row" key={surface.key}>
              <span className="stat-dot" style={{ background: surface.color }} />
              <span className="stat-label">{surface.label}</span>
              <span className="stat-value">{formatKm(value)} км</span>
              <span className="stat-percent">{percent}%</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function Inspector({ editor, onLogin }) {
  const { auth, currentRoute, name, isDirty, segmentCount, stats, statsLoading, autoSnap, busy, actions } = editor;

  if (auth !== "admin") {
    return (
      <aside className="inspector">
        <section className="panel">
          <span className="label">Режим просмотра</span>
          <p className="hint" style={{ margin: 0 }}>
            Создание, редактирование, импорт и статистика маршрутов доступны после входа администратора.
          </p>
          {auth === "guest" && (
            <Button variant="secondary" icon={Lock} onClick={onLogin}>
              Войти
            </Button>
          )}
        </section>
      </aside>
    );
  }

  const canSave = isDirty || !currentRoute;

  return (
    <aside className="inspector">
      <section className="panel">
        <span className="label">{currentRoute ? "Маршрут" : "Новый маршрут"}</span>
        <Input
          placeholder="Название маршрута"
          value={name}
          maxLength={200}
          onChange={(event) => actions.changeName(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && actions.save()}
          aria-label="Название маршрута"
        />
        <dl className="kv" style={{ margin: 0 }}>
          {currentRoute && (
            <>
              <div>
                <dt>Создан</dt>
                <dd>{formatDateTime(currentRoute.created_at)}</dd>
              </div>
              <div>
                <dt>Изменён</dt>
                <dd>{formatDateTime(currentRoute.updated_at)}</dd>
              </div>
            </>
          )}
          <div>
            <dt>Сегментов</dt>
            <dd>{segmentCount}</dd>
          </div>
        </dl>
        <div className="panel-row">
          <Button variant="primary" icon={Save} block onClick={actions.save} loading={busy.save} disabled={!canSave}>
            Сохранить
          </Button>
          {currentRoute && (
            <Button variant="danger" icon={Trash2} onClick={actions.deleteCurrent} loading={busy.delete}>
              Удалить
            </Button>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-row">
          <span className="label">Примагничивание</span>
          <span className="hint subtle">OSRM · 15 м</span>
        </div>
        <div className="setting">
          <div className="setting-text">
            <span>Авто после рисования</span>
            <span className="hint">Новые линии выравниваются по дорогам</span>
          </div>
          <Toggle checked={autoSnap} onChange={actions.changeAutoSnap} label="Авто-примагничивание после рисования" />
        </div>
        <Button
          variant="secondary"
          icon={Magnet}
          block
          onClick={actions.snapWholeRoute}
          loading={busy.snap}
          disabled={!segmentCount}
        >
          Примагнитить весь маршрут
        </Button>
      </section>

      <StatsPanel stats={stats} loading={statsLoading} hasRoute={Boolean(currentRoute)} />
    </aside>
  );
}
