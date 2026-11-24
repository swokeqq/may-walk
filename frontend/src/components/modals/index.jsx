import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Download, File as FileIcon, Info, Lock, Upload, X, XCircle } from "lucide-react";
import { Button, Checkbox, Chip, IconButton, Input, Modal } from "../ui";

// ───────────── Вход администратора (поповер под кнопкой «Войти») ─────────────

export function LoginPopover({ onLogin, onClose }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
    const onKey = (event) => event.key === "Escape" && onClose();
    const onClick = (event) => {
      if (!ref.current?.contains(event.target) && !event.target.closest("[data-login-trigger]")) onClose();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onClick);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onClick);
    };
  }, [onClose]);

  const submit = async (event) => {
    event.preventDefault();
    if (!password.trim()) {
      setError("Введите пароль");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onLogin(password.trim());
      onClose();
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <form className="popover" ref={ref} onSubmit={submit} aria-label="Вход администратора">
      <div>
        <h3>Вход администратора</h3>
        <div className="hint">Создание и правка маршрутов доступны после входа.</div>
      </div>
      <div className="field">
        <span className="label">Пароль</span>
        <Input
          icon={Lock}
          type="password"
          inputRef={inputRef}
          value={password}
          invalid={Boolean(error)}
          autoComplete="current-password"
          placeholder="Пароль администратора"
          onChange={(event) => setPassword(event.target.value)}
        />
        {error && <div className="field-error">{error}</div>}
      </div>
      <button type="submit" className="btn btn-primary block no-icon" disabled={loading}>
        {loading ? "Вход…" : "Войти"}
      </button>
    </form>
  );
}

// ───────────── Экспорт ─────────────

const FORMATS = [
  { id: "geojson", label: "GeoJSON", ext: ".geojson", description: "Веб-карты, QGIS, повторный импорт" },
  { id: "gpx", label: "GPX", ext: ".gpx", description: "Навигаторы, Strava, Garmin" },
  { id: "kml", label: "KML", ext: ".kml", description: "Google Earth, Яндекс.Карты" },
];

export function ExportModal({ route, segmentCount, onExport, onClose, loading }) {
  const [format, setFormat] = useState("geojson");
  const selected = FORMATS.find((item) => item.id === format);

  return (
    <Modal
      title="Экспорт маршрута"
      subtitle={`${route.name} · ${segmentCount} сегм.`}
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Отмена
          </Button>
          <Button
            variant="primary"
            icon={Download}
            loading={loading}
            data-autofocus
            onClick={async () => (await onExport(format)) && onClose()}
          >
            Скачать {selected.ext}
          </Button>
        </>
      }
    >
      <div role="radiogroup" aria-label="Формат файла" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {FORMATS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="radio"
            aria-checked={item.id === format}
            className="option-card"
            onClick={() => setFormat(item.id)}
          >
            <span className="radio" aria-hidden />
            <span>
              <span className="title">
                {item.label} <small>{item.ext}</small>
              </span>
              <span className="hint">{item.description}</span>
            </span>
          </button>
        ))}
      </div>
    </Modal>
  );
}

// ───────────── Импорт ─────────────

const ACCEPT = ".gpx,.kml,.geojson,.json";

const formatSize = (bytes) => (bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} КБ` : `${(bytes / 1024 / 1024).toFixed(1)} МБ`);

export function ImportModal({ defaultSnap, onImport, onClose, loading }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [snap, setSnap] = useState(defaultSnap);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const pick = (candidate) => {
    if (!candidate) return;
    const ext = candidate.name.split(".").pop().toLowerCase();
    if (!["gpx", "kml", "geojson", "json"].includes(ext)) {
      setError("Поддерживаются файлы .geojson, .gpx и .kml");
      return;
    }
    setError("");
    setFile(candidate);
    setName(candidate.name.replace(/\.[^/.]+$/, ""));
  };

  const onDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    pick(event.dataTransfer.files?.[0]);
  };

  return (
    <Modal
      title="Импорт маршрута"
      subtitle="Файл будет сохранён как новый маршрут"
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Отмена
          </Button>
          <Button
            variant="primary"
            icon={Upload}
            loading={loading}
            disabled={!file || !name.trim()}
            onClick={async () => (await onImport(file, { name: name.trim(), snap })) && onClose()}
          >
            Импортировать
          </Button>
        </>
      }
    >
      <div
        className={`dropzone${dragging ? " dragging" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <span className="icon-box">
          <Upload size={20} strokeWidth={1.75} />
        </span>
        <strong>Перетащите файл сюда</strong>
        <span className="hint">
          или{" "}
          <button type="button" className="link-btn" data-autofocus onClick={() => inputRef.current?.click()}>
            выберите на компьютере
          </button>
        </span>
        <span className="group">
          <Chip>.geojson</Chip>
          <Chip>.gpx</Chip>
          <Chip>.kml</Chip>
        </span>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          tabIndex={-1}
          onChange={(event) => {
            pick(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </div>

      {error && <div className="field-error">{error}</div>}

      {file && (
        <>
          <div className="file-row">
            <FileIcon size={18} strokeWidth={1.75} />
            <div className="file-text">
              <div className="file-name">{file.name}</div>
              <div className="hint">{formatSize(file.size)}</div>
            </div>
            <IconButton icon={X} label="Убрать файл" small onClick={() => setFile(null)} />
          </div>
          <div className="field" style={{ marginTop: 8 }}>
            <span className="label">Название</span>
            <Input value={name} maxLength={200} onChange={(event) => setName(event.target.value)} aria-label="Название маршрута" />
          </div>
          <div className="check-row" style={{ marginTop: 4 }}>
            <Checkbox checked={snap} onChange={setSnap} label="Примагнитить к дорогам при импорте" />
            <span>Примагнитить к дорогам при импорте</span>
          </div>
        </>
      )}
    </Modal>
  );
}

// ───────────── Подтверждение ─────────────

export function ConfirmDialog({ request, onSettle }) {
  return (
    <Modal
      small
      title={request.title}
      onClose={() => onSettle(false)}
      footer={
        <>
          <Button variant="ghost" onClick={() => onSettle(false)}>
            Отмена
          </Button>
          <Button variant={request.danger ? "danger" : "primary"} data-autofocus onClick={() => onSettle(true)}>
            {request.confirmLabel || "Продолжить"}
          </Button>
        </>
      }
    >
      <p className="confirm-text">{request.message}</p>
    </Modal>
  );
}

// ───────────── Тосты ─────────────

const TOAST_ICONS = { success: CheckCircle2, error: XCircle, info: Info };

export function Toasts({ toasts, onDismiss }) {
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map((toast) => {
        const Icon = TOAST_ICONS[toast.tone] || Info;
        return (
          <div key={toast.id} className={`toast toast-${toast.tone}`} role={toast.tone === "error" ? "alert" : "status"}>
            <Icon size={16} strokeWidth={1.75} aria-hidden />
            <span>{toast.text}</span>
            <IconButton icon={X} label="Закрыть" small onClick={() => onDismiss(toast.id)} />
          </div>
        );
      })}
    </div>
  );
}
