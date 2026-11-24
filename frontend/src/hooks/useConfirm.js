import { useCallback, useRef, useState } from "react";

/** Promise-based замена window.confirm: `if (!(await confirm({...}))) return;` */
export function useConfirm() {
  const [request, setRequest] = useState(null);
  const resolver = useRef(null);

  const confirm = useCallback(
    (options) =>
      new Promise((resolve) => {
        resolver.current = resolve;
        setRequest(options);
      }),
    [],
  );

  const settle = useCallback((value) => {
    resolver.current?.(value);
    resolver.current = null;
    setRequest(null);
  }, []);

  return { confirmRequest: request, confirm, settle };
}
