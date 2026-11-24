import { useEffect, useRef, useState } from "react";
import "ol/ol.css";
import { Check, ChevronDown, Eraser, Hand, Layers, Loader2, LocateFixed, Magnet, Minus, PenLine, Plus } from "lucide-react";
import { BASE_LAYERS, MapEngine } from "../../map/MapEngine";
import { IconButton, Kbd } from "../ui";

const TOOLS = [
  { id: "hand", icon: Hand, label: "Рука", hint: "перемещение и правка вершин", key: "H" },
  { id: "brush", icon: PenLine, label: "Кисть", hint: "рисование линии", key: "B" },
  { id: "eraser", icon: Eraser, label: "Ластик", hint: "удаление сегмента", key: "E" },
];

function ToolButton({ tool, active, onClick }) {
  return (
    <div className="tool">
      <IconButton icon={tool.icon} label={`${tool.label} — ${tool.hint} (${tool.key})`} active={active} onClick={onClick} />
      <span className="tooltip" aria-hidden>
        {tool.label}
        <Kbd>{tool.key}</Kbd>
      </span>
    </div>
  );
}

function LayerSwitcher({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const close = (event) => {
      if (!ref.current?.contains(event.target)) setOpen(false);
    };
    window.addEventListener("mousedown", close);
    return () => window.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div className="floating layer-switcher" ref={ref}>
      <button type="button" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((x) => !x)}>
        <Layers size={16} strokeWidth={1.75} aria-hidden />
        {BASE_LAYERS[value].label}
        <ChevronDown size={14} strokeWidth={1.75} aria-hidden />
      </button>
      {open && (
        <ul className="floating layer-menu" role="menu">
          {Object.entries(BASE_LAYERS).map(([key, layer]) => (
            <li key={key}>
              <button
                type="button"
                role="menuitemradio"
                aria-checked={key === value}
                onClick={() => {
                  onChange(key);
                  setOpen(false);
                }}
              >
                {layer.label}
                {key === value && <Check size={14} strokeWidth={2} style={{ marginLeft: "auto" }} aria-hidden />}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function MapView({ editor, isAdmin }) {
  const targetRef = useRef(null);
  const { attachEngine, handlersRef, tool, baseLayer, autoSnap, busy, actions } = editor;

  useEffect(() => {
    const engine = new MapEngine(targetRef.current, handlersRef);
    attachEngine(engine);
    return () => {
      attachEngine(null);
      engine.destroy();
    };
  }, [attachEngine, handlersRef]);

  // Гость может только смотреть карту
  useEffect(() => {
    if (!isAdmin && tool !== "hand") actions.changeTool("hand");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  return (
    <main className="map-wrap">
      <div ref={targetRef} className={`map tool-${tool}`} aria-label="Карта" />

      <div className="floating tool-palette" role="toolbar" aria-label="Инструменты">
        {(isAdmin ? TOOLS : TOOLS.slice(0, 1)).map((item) => (
          <ToolButton key={item.id} tool={item} active={tool === item.id} onClick={() => actions.changeTool(item.id)} />
        ))}
        {isAdmin && (
          <>
            <span className="vdivider" />
            <div className="tool">
              <IconButton
                icon={Magnet}
                label={autoSnap ? "Авто-примагничивание включено" : "Авто-примагничивание выключено"}
                active={autoSnap}
                onClick={() => actions.changeAutoSnap(!autoSnap)}
              />
              <span className="tooltip" aria-hidden>
                Авто-snap {autoSnap ? "вкл" : "выкл"}
              </span>
            </div>
          </>
        )}
      </div>

      {busy.snap && (
        <div className="floating map-busy" role="status">
          <Loader2 size={14} className="spin" aria-hidden /> Примагничивание…
        </div>
      )}

      {tool === "brush" && (
        <div className="floating drawing-hint">
          <b>клик</b> — точка <span className="dot">·</span>
          <b>2×клик</b> — завершить <span className="dot">·</span>
          <Kbd>⌫</Kbd> шаг назад <span className="dot">·</span>
          <Kbd>Esc</Kbd> отмена
        </div>
      )}

      <LayerSwitcher value={baseLayer} onChange={actions.changeBaseLayer} />

      <div className="floating map-controls">
        <div className="floating">
          <IconButton icon={LocateFixed} label="Показать маршрут целиком" onClick={actions.recenter} />
        </div>
        <div className="floating">
          <IconButton icon={Plus} label="Приблизить" onClick={actions.zoomIn} />
          <span className="hdivider" />
          <IconButton icon={Minus} label="Отдалить" onClick={actions.zoomOut} />
        </div>
      </div>

      <div className="attribution">
        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
          {BASE_LAYERS[baseLayer].attribution}
        </a>
      </div>
    </main>
  );
}
