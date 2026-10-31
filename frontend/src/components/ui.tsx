import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

export function Brand() {
  return (
    <div className="brand" aria-label="Brightloop">
      <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
      <span>Brightloop</span>
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

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  hint?: string;
  containerClassName?: string;
}

export function TextAreaField({ label, error, hint, id, className, containerClassName, ...props }: TextAreaFieldProps) {
  const fieldId = id ?? props.name;
  return <label className={`field ${containerClassName ?? ""}`.trim()} htmlFor={fieldId}><span className="field__label">{label}</span><textarea id={fieldId} className={`${error ? "input input--error" : "input"} textarea ${className ?? ""}`.trim()} aria-invalid={Boolean(error)} {...props} />{error ? <span className="field__error">{error}</span> : hint ? <span className="field__hint">{hint}</span> : null}</label>;
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: string[];
  containerClassName?: string;
}

export function SelectField({ label, options, id, className, containerClassName, ...props }: SelectFieldProps) {
  const fieldId = id ?? props.name;
  return <label className={`field ${containerClassName ?? ""}`.trim()} htmlFor={fieldId}><span className="field__label">{label}</span><select id={fieldId} className={`input select-input ${className ?? ""}`.trim()} {...props}>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>;
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

export function LoadingState({ title = "Loading", description = "Retrieving the latest information." }: { title?: string; description?: string }) {
  return <StatePanel title={title}><div className="state-row"><span className="loading-spinner" aria-hidden="true" /><p>{description}</p></div></StatePanel>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <StatePanel title={title}><p>{description}</p>{action ? <div className="state-action">{action}</div> : null}</StatePanel>;
}

export function ErrorState({ title = "Something went wrong", description, onRetry }: { title?: string; description: string; onRetry?: () => void }) {
  return <StatePanel title={title} tone="danger"><p>{description}</p>{onRetry ? <div className="state-action"><Button type="button" tone="secondary" onClick={onRetry}>Try again</Button></div> : null}</StatePanel>;
}

export interface TableColumn<T> {
  id: string;
  header: string;
  cell: (row: T) => ReactNode;
}

export function DataTable<T>({ columns, rows, label, getRowKey }: { columns: TableColumn<T>[]; rows: T[]; label: string; getRowKey: (row: T) => string | number }) {
  return <div className="table-wrap"><table aria-label={label}><thead><tr>{columns.map((column) => <th key={column.id}>{column.header}</th>)}</tr></thead><tbody>{rows.map((row) => <tr key={getRowKey(row)}>{columns.map((column) => <td key={column.id}>{column.cell(row)}</td>)}</tr>)}</tbody></table></div>;
}

export function StatusBadge({ value }: { value: string }) {
  const label = value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
  return <span className={`status-badge status-badge--${value.toLowerCase()}`}>{label}</span>;
}
