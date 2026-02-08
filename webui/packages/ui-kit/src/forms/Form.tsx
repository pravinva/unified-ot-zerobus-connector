import type { ReactNode } from "react";

export function Field(props: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="field">
      <div className="field-label">{props.label}</div>
      {props.hint && <div className="field-hint">{props.hint}</div>}
      <div className="field-control">{props.children}</div>
    </label>
  );
}

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`input ${props.className ?? ""}`.trim()} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`input ${props.className ?? ""}`.trim()} />;
}

export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" }) {
  const variant = props.variant ?? "secondary";
  const cls = variant === "primary" ? "btn btn-primary" : variant === "danger" ? "btn btn-danger" : "btn btn-secondary";
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { variant: _variant, className, ...rest } = props;
  return <button {...rest} className={`${cls} ${className ?? ""}`.trim()} />;
}

