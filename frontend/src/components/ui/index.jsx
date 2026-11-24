// Базовые компоненты — соответствуют компонентам Figma-макета (Button, IconButton, Input, Toggle, Checkbox, Chip, Kbd).
import { useEffect, useRef } from "react";
import { Check, Loader2, X } from "lucide-react";

const cx = (...classes) => classes.filter(Boolean).join(" ");

export function Button({ variant = "secondary", icon: Icon, loading = false, block = false, className, children, disabled, ...props }) {
  const ShownIcon = loading ? Loader2 : Icon;
  return (
    <button
      type="button"
      className={cx("btn", `btn-${variant}`, !ShownIcon && "no-icon", block && "block", className)}
      disabled={disabled || loading}
      {...props}
    >
      {ShownIcon && <ShownIcon size={16} strokeWidth={1.75} className={loading ? "spin" : undefined} aria-hidden />}
      {children}
    </button>
  );
}

export function IconButton({ icon: Icon, label, active = false, small = false, className, ...props }) {
  return (
    <button
      type="button"
      className={cx("icon-btn", active && "active", small && "small", className)}
      aria-label={label}
      aria-pressed={active || undefined}
      title={label}
      {...props}
    >
      <Icon size={small ? 16 : 18} strokeWidth={1.75} aria-hidden />
    </button>
  );
}

export function Input({ icon: Icon, invalid = false, inputRef, className, ...props }) {
  return (
    <label className={cx("input", invalid && "invalid", className)}>
      {Icon && <Icon size={16} strokeWidth={1.75} aria-hidden />}
      <input ref={inputRef} {...props} />
    </label>
  );
}

export function Toggle({ checked, onChange, label, disabled }) {
  return (
    <button
      type="button"
      role="switch"
      className="toggle"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
    />
  );
}

export function Checkbox({ checked, onChange, label }) {
  return (
    <button
      type="button"
      role="checkbox"
      className="checkbox"
      aria-checked={checked}
      aria-label={label}
      title={label}
      onClick={() => onChange(!checked)}
    >
      {checked && <Check size={12} strokeWidth={2.5} aria-hidden />}
    </button>
  );
}

export function Chip({ tone = "neutral", children }) {
  return <span className={`chip chip-${tone}`}>{children}</span>;
}

export function Kbd({ children }) {
  return <kbd className="kbd">{children}</kbd>;
}

export function Modal({ title, subtitle, onClose, footer, children, small = false }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    dialogRef.current?.querySelector("input, button[data-autofocus]")?.focus();
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="scrim" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className={cx("modal", small && "small")} role="dialog" aria-modal="true" aria-label={title} ref={dialogRef}>
        <div className="modal-header">
          <div>
            <h3>{title}</h3>
            {subtitle && <div className="hint">{subtitle}</div>}
          </div>
          <IconButton icon={X} label="Закрыть" onClick={onClose} />
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}
