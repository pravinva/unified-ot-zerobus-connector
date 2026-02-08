import type { ReactNode } from "react";

export function Panel(props: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const { title, subtitle, actions, children, className } = props;
  return (
    <section className={`card ${className ?? ""}`.trim()}>
      {(title || subtitle || actions) && (
        <header className="card-head">
          <div className="card-title-wrap">
            {title && <div className="section-title">{title}</div>}
            {subtitle && <div className="hint">{subtitle}</div>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      <div className="card-body">{children}</div>
    </section>
  );
}

