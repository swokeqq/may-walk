import { useCallback, useEffect, useState } from "react";
import { Topbar } from "./components/layout/Topbar";
import { Sidebar } from "./components/layout/Sidebar";
import { Inspector } from "./components/layout/Inspector";
import { StatusBar } from "./components/layout/StatusBar";
import { MapView } from "./components/map/MapView";
import { ConfirmDialog, ExportModal, ImportModal, LoginPopover, Toasts } from "./components/modals";
import { useConfirm } from "./hooks/useConfirm";
import { useRouteEditor } from "./hooks/useRouteEditor";
import { useToasts } from "./hooks/useToasts";

const isTyping = (target) => target instanceof HTMLElement && (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

export default function App() {
  const { toasts, status, notify, dismiss } = useToasts();
  const { confirmRequest, confirm, settle } = useConfirm();
  const editor = useRouteEditor({ notify, confirm });
  const { auth, actions } = editor;
  const isAdmin = auth === "admin";

  const [loginOpen, setLoginOpen] = useState(false);
  const [modal, setModal] = useState(null); // "import" | "export" | null

  const openLogin = useCallback(() => setLoginOpen((open) => !open), []);
  const closeLogin = useCallback(() => setLoginOpen(false), []);
  const closeModal = useCallback(() => setModal(null), []);

  const openImport = async () => {
    if (await actions.confirmDiscard()) setModal("import");
  };

  // Горячие клавиши редактора
  useEffect(() => {
    if (!isAdmin) return undefined;

    const onKeyDown = (event) => {
      if (confirmRequest || modal || isTyping(event.target)) return;
      const mod = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();

      if (mod && key === "z") {
        event.preventDefault();
        if (event.shiftKey) actions.redo();
        else actions.undo();
      } else if (mod && key === "y") {
        event.preventDefault();
        actions.redo();
      } else if (mod && key === "s") {
        event.preventDefault();
        actions.save();
      } else if (!mod && !event.altKey) {
        if (key === "h" || key === "р") actions.changeTool("hand");
        else if (key === "b" || key === "и") actions.changeTool("brush");
        else if (key === "e" || key === "у") actions.changeTool("eraser");
        else if (event.key === "Escape") actions.abortDrawing();
        else if (event.key === "Backspace") actions.removeLastPoint();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isAdmin, actions, confirmRequest, modal]);

  return (
    <div className="app">
      <Topbar editor={editor} onLogin={openLogin} onImport={openImport} onExport={() => setModal("export")} />

      <div className="body">
        <Sidebar editor={editor} onLogin={openLogin} />
        <MapView editor={editor} isAdmin={isAdmin} />
        <Inspector editor={editor} onLogin={openLogin} />
      </div>

      <StatusBar editor={editor} status={status} />

      {loginOpen && auth === "guest" && <LoginPopover onLogin={actions.login} onClose={closeLogin} />}

      {modal === "export" && editor.currentRoute && (
        <ExportModal
          route={editor.currentRoute}
          segmentCount={editor.segmentCount}
          loading={editor.busy.export}
          onExport={actions.exportCurrent}
          onClose={closeModal}
        />
      )}

      {modal === "import" && (
        <ImportModal defaultSnap={editor.autoSnap} loading={editor.busy.import} onImport={actions.importFile} onClose={closeModal} />
      )}

      {confirmRequest && <ConfirmDialog request={confirmRequest} onSettle={settle} />}

      <Toasts toasts={toasts} onDismiss={dismiss} />
    </div>
  );
}
