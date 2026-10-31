import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Brand() {
  return (
    <div className="brand" aria-label="SaasDeck">
      <span className="brand-mark" aria-hidden="true">S</span>
      <span>SaasDeck</span>
    </div>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { tone?: "primary" | "secondary" | "quiet" };

export function Button({ tone = "primary", className = "", ...props }: ButtonProps) {
  return <button className={`button button--${tone} ${className}`.trim()} {...props} />;
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
  containerClassName?: string;
}

export function TextField({ label, error, hint, id, className, containerClassName, ...props }: TextFieldProps) {
  const fieldId = id ?? props.name;
  return (
    <label className={`field ${containerClassName ?? ""}`.trim()} htmlFor={fieldId}>
      <span className="field__label">{label}</span>
      <input id={fieldId} className={`${error ? "input input--error" : "input"} ${className ?? ""}`.trim()} aria-invalid={Boolean(error)} {...props} />
      {error ? <span className="field__error">{error}</span> : hint ? <span className="field__hint">{hint}</span> : null}
    </label>
  );
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description: string; action?: ReactNode }) {
  return (
    <header className="page-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action ? <div className="page-header__action">{action}</div> : null}
    </header>
  );
}

export function StatePanel({ title, children, tone = "neutral" }: { title: string; children: ReactNode; tone?: "neutral" | "danger" }) {
  return <section className={`state-panel state-panel--${tone}`}><h2>{title}</h2><div>{children}</div></section>;
}
