import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { AppShell, Button, Panel, StatusPill, Toast, useToast } from "@ot/ui-kit";
import { ToastProvider } from "./toast/ToastContext";
import { useAuth } from "./auth/useAuth";
import { AuthProvider } from "./auth/AuthContext";
import { NavProvider } from "./nav/NavContext";

const OverviewPage = lazy(() => import("./pages/OverviewPage").then((m) => ({ default: m.OverviewPage })));
const DiscoveryPage = lazy(() => import("./pages/DiscoveryPage").then((m) => ({ default: m.DiscoveryPage })));
const SourcesPage = lazy(() => import("./pages/SourcesPage").then((m) => ({ default: m.SourcesPage })));
const ZeroBusPage = lazy(() => import("./pages/ZeroBusPage").then((m) => ({ default: m.ZeroBusPage })));
const StatusPage = lazy(() => import("./pages/StatusPage").then((m) => ({ default: m.StatusPage })));
const MetricsPage = lazy(() => import("./pages/MetricsPage").then((m) => ({ default: m.MetricsPage })));
const PipelinePage = lazy(() => import("./pages/PipelinePage").then((m) => ({ default: m.PipelinePage })));
const AuthPage = lazy(() => import("./pages/AuthPage").then((m) => ({ default: m.AuthPage })));

type NavKey =
  | "overview"
  | "discovery"
  | "sources"
  | "zerobus"
  | "status"
  | "metrics"
  | "pipeline"
  | "auth";

function loadNavKey(): NavKey {
  const v = window.localStorage.getItem("connector-ui.nav");
  const allowed: NavKey[] = ["overview", "discovery", "sources", "zerobus", "status", "metrics", "pipeline", "auth"];
  return (allowed.includes(v as NavKey) ? (v as NavKey) : "overview");
}

function App() {
  const [active, setActive] = useState<NavKey>(() => loadNavKey());
  const toastApi = useToast();
  const auth = useAuth();

  useEffect(() => {
    window.localStorage.setItem("connector-ui.nav", active);
  }, [active]);

  const nav = useMemo(
    () => [
      { key: "overview", label: "Overview" },
      { key: "discovery", label: "Discovery" },
      { key: "sources", label: "Sources" },
      { key: "zerobus", label: "ZeroBus" },
      { key: "status", label: "Status" },
      { key: "metrics", label: "Metrics" },
      { key: "pipeline", label: "Pipeline" },
      { key: "auth", label: "Auth" },
    ],
    []
  );

  return (
    <>
      <ToastProvider api={{ show: toastApi.show }}>
        <AuthProvider value={auth}>
          <NavProvider api={{ go: (k) => setActive(k as NavKey) }}>
          <AppShell
        title="Unified OT Connector"
        subtitle="Control room console"
        nav={nav}
        activeKey={active}
        onNavigate={(k) => setActive(k as NavKey)}
        topRight={
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <StatusPill kind={auth.loading ? "warn" : "ok"}>
              {auth.loading ? "Auth: loading" : auth.authStatus?.auth_enabled ? "Auth: enabled" : "Auth: disabled"}
            </StatusPill>
            <StatusPill kind="ok">UI: React</StatusPill>
            <a href="/legacy" style={{ textDecoration: "none" }}>
              <Button variant="secondary" type="button">
                Legacy UI
              </Button>
            </a>
          </div>
        }
      >
        <Suspense fallback={<div className="muted">Loading…</div>}>
          {active === "overview" && <OverviewPage />}
          {active === "discovery" && <DiscoveryPage />}
          {active === "sources" && <SourcesPage />}
          {active === "zerobus" && <ZeroBusPage />}
          {active === "status" && <StatusPage />}
          {active === "metrics" && <MetricsPage />}
          {active === "pipeline" && <PipelinePage />}
          {active === "auth" && <AuthPage />}
        </Suspense>

        <div style={{ marginTop: 16 }}>
          <Panel title="Notes" subtitle="Parity-first migration. Use /legacy if needed.">
            <div className="muted">
              This UI is a React rebuild. All backend routes/contracts must remain unchanged. If something looks off, open
              <code style={{ marginLeft: 6 }}>/legacy</code> to compare behavior.
            </div>
          </Panel>
        </div>
      </AppShell>
        <Toast toast={toastApi.toast} />
          </NavProvider>
        </AuthProvider>
      </ToastProvider>
    </>
  );
}

export default App;
