import type { ReactNode } from "react";

export type NavItem = { key: string; label: string };

export function AppShell(props: {
  title: ReactNode;
  subtitle?: ReactNode;
  nav: NavItem[];
  activeKey: string;
  onNavigate: (key: string) => void;
  topRight?: ReactNode;
  children: ReactNode;
}) {
  const { title, subtitle, nav, activeKey, onNavigate, topRight, children } = props;
  return (
    <div className="container">
      <div className="topbar">
        <div className="title">
          <h1>{title}</h1>
          {subtitle && <div className="subtitle">{subtitle}</div>}
        </div>
        {topRight && <div className="topbar-right">{topRight}</div>}
      </div>

      <div className="app-shell">
        <aside className="side">
          <div className="side-nav">
            {nav.map((n) => (
              <button
                key={n.key}
                type="button"
                className={`side-nav-item ${n.key === activeKey ? "active" : ""}`.trim()}
                onClick={() => onNavigate(n.key)}
              >
                {n.label}
              </button>
            ))}
          </div>
        </aside>
        <main className="main">{children}</main>
      </div>
    </div>
  );
}

