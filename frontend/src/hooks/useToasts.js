import { useCallback, useRef, useState } from "react";

const TOAST_TTL = { success: 3500, info: 4000, error: 6000 };

/** Уведомления: тост + сообщение в статус-баре (заменяют старые routesMessage/authMessage). */
export function useToasts() {
  const [toasts, setToasts] = useState([]);
  const [status, setStatus] = useState({ text: "Готово", tone: "info" });
  const nextId = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts((items) => items.filter((toast) => toast.id !== id));
  }, []);

  /**
   * @param {string} text
   * @param {"info"|"success"|"error"} tone
   * @param {{ toast?: boolean }} options — info по умолчанию пишется только в статус-бар
   */
  const notify = useCallback(
    (text, tone = "info", { toast = tone !== "info" } = {}) => {
      setStatus({ text, tone });
      if (!toast) return;
      nextId.current += 1;
      const id = nextId.current;
      setToasts((items) => [...items.slice(-2), { id, text, tone }]);
      setTimeout(() => dismiss(id), TOAST_TTL[tone] || 4000);
    },
    [dismiss],
  );

  return { toasts, status, notify, dismiss };
}
