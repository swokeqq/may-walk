import { Download, Lock, LogOut, Redo2, Route, Undo2, Upload } from "lucide-react";
import { Button, Chip, IconButton } from "../ui";

export function Topbar({ editor, onLogin, onImport, onExport }) {
  const { auth, currentRoute, name, isDirty, canUndo, canRedo, actions } = editor;
  const isAdmin = auth === "admin";
  const title = currentRoute ? name || currentRoute.name : isDirty ? name || "Новый маршрут" : null;

  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-logo" aria-hidden>
          <Route size={16} strokeWidth={2} />
        </span>
        may·walk
      </div>

      <span className="vdivider" />

      <nav className="breadcrumbs" aria-label="Навигация">
        <span>Маршруты</span>
        {title && (
          <>
            <span className="sep">/</span>
            <span className="current">{title}</span>
            {isDirty && <Chip>изменён</Chip>}
          </>
        )}
      </nav>

      <span className="spacer" />

      {isAdmin && (
        <>
          <div className="group tight">
            <IconButton icon={Undo2} label="Отменить (Ctrl+Z)" disabled={!canUndo} onClick={actions.undo} />
            <IconButton icon={Redo2} label="Повторить (Ctrl+Shift+Z)" disabled={!canRedo} onClick={actions.redo} />
          </div>
          <span className="vdivider" />
          <div className="group">
            <Button variant="ghost" icon={Upload} onClick={onImport}>
              Импорт
            </Button>
            <Button
              variant="secondary"
              icon={Download}
              onClick={onExport}
              disabled={!currentRoute}
              title={currentRoute ? undefined : "Откройте сохранённый маршрут"}
            >
              Экспорт
            </Button>
          </div>
          <span className="vdivider" />
          <div className="group">
            <Chip tone="success">admin</Chip>
            <IconButton icon={LogOut} label="Выйти" onClick={actions.logout} />
          </div>
        </>
      )}

      {auth === "guest" && (
        <div className="group">
          <Chip>только просмотр</Chip>
          <Button variant="primary" icon={Lock} onClick={onLogin} data-login-trigger>
            Войти
          </Button>
        </div>
      )}
    </header>
  );
}
