import { useEffect, useState } from "react";
import { Check, Info, Lock } from "lucide-react";
import { BASE_LAYERS } from "../../map/MapEngine";
import { formatCoord, TOOL_LABELS } from "../../utils/format";

export function StatusBar({ editor, status }) {
  const { subscribeView, tool, baseLayer, autoSnap, auth } = editor;
  const [view, setView] = useState({ pointer: null, zoom: 12 });

  useEffect(
    () => subscribeView((patch) => setView((state) => ({ ...state, ...patch }))),
    [subscribeView],
  );

  const Icon = auth === "guest" && status.tone === "info" ? Lock : status.tone === "success" ? Check : Info;

  return (
    <footer className="statusbar">
      <span className="tool-state">{TOOL_LABELS[tool]}</span>
      <span>{BASE_LAYERS[baseLayer].label.toLowerCase()}</span>
      {auth === "admin" && <span>snap: {autoSnap ? "auto" : "off"}</span>}
      <span>{view.pointer ? formatCoord(view.pointer) : "—"}</span>
      <span>z {Math.round(view.zoom ?? 12)}</span>
      <span className="spacer" />
      <span className={`message ${status.tone}`} role="status" aria-live="polite">
        <Icon size={14} strokeWidth={1.75} aria-hidden />
        <span>
          {auth === "guest" && status.text === "Готово" ? "Режим просмотра — войдите, чтобы редактировать" : status.text}
        </span>
      </span>
    </footer>
  );
}
