import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { AppShell, Button, Panel, StatusPill, Toast, useToast } from "@ot/ui-kit";
import { ToastProvider } from "./toast/ToastContext";

const OverviewPage = lazy(() => import("./pages/OverviewPage").then((m) => ({ default: m.OverviewPage })));
const SensorsPage = lazy(() => import("./pages/SensorsPage").then((m) => ({ default: m.SensorsPage })));
const ZeroBusPage = lazy(() => import("./pages/ZeroBusPage").then((m) => ({ default: m.ZeroBusPage })));
const ModesPage = lazy(() => import("./pages/ModesPage").then((m) => ({ default: m.ModesPage })));
const ConnectionsPage = lazy(() => import("./pages/ConnectionsPage").then((m) => ({ default: m.ConnectionsPage })));
const OpcuaWotPage = lazy(() => import("./pages/OpcuaWotPage").then((m) => ({ default: m.OpcuaWotPage })));
const TrainingPage = lazy(() => import("./pages/TrainingPage").then((m) => ({ default: m.TrainingPage })));
const NlpPage = lazy(() => import("./pages/NlpPage").then((m) => ({ default: m.NlpPage })));

type NavKey = "overview" | "sensors" | "zerobus" | "modes" | "connections" | "opcua_wot" | "training" | "nlp";

function loadNavKey(): NavKey {
  const v = window.localStorage.getItem("simulator-ui.nav");
  const allowed: NavKey[] = ["overview", "sensors", "zerobus", "modes", "connections", "opcua_wot", "training", "nlp"];
  return (allowed.includes(v as NavKey) ? (v as NavKey) : "overview");
}

function App() {
  const [active, setActive] = useState<NavKey>(() => loadNavKey());
  const toastApi = useToast();

  useEffect(() => {
    window.localStorage.setItem("simulator-ui.nav", active);
  }, [active]);

  const nav = useMemo(
    () => [
      { key: "overview", label: "Overview" },
      { key: "sensors", label: "Sensors" },
      { key: "zerobus", label: "ZeroBus" },
      { key: "modes", label: "Vendor modes" },
      { key: "connections", label: "Connections" },
      { key: "opcua_wot", label: "OPC-UA / WoT" },
      { key: "training", label: "Training" },
      { key: "nlp", label: "NLP / WS" },
    ],
    []
  );

  return (
    <>
      <ToastProvider api={{ show: toastApi.show }}>
        <AppShell
        title="OT Simulator"
        subtitle="Industrial data generator console"
        nav={nav}
        activeKey={active}
        onNavigate={(k) => setActive(k as NavKey)}
        topRight={
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
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
          {active === "sensors" && <SensorsPage />}
          {active === "zerobus" && <ZeroBusPage />}
          {active === "modes" && <ModesPage />}
          {active === "connections" && <ConnectionsPage />}
          {active === "opcua_wot" && <OpcuaWotPage />}
          {active === "training" && <TrainingPage />}
          {active === "nlp" && <NlpPage />}
        </Suspense>

        <div style={{ marginTop: 16 }}>
          <Panel title="Notes" subtitle="React rebuild. Use /legacy to compare.">
            <div className="muted">
              This UI will keep the existing REST + WebSocket contracts untouched. If a feature is missing, fall back to{" "}
              <code>/legacy</code> while we complete parity.
            </div>
          </Panel>
        </div>
      </AppShell>

      <Toast toast={toastApi.toast} />
      </ToastProvider>
    </>
  );
}

export default App;
