import { Button, Panel } from "@ot/ui-kit";
import { useCallback, useEffect, useState } from "react";
import { simApi } from "../api/simApi";
import { useAppToast } from "../toast/ToastContext";

export function ModesPage() {
  const toast = useAppToast();
  const [modes, setModes] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [recent, setRecent] = useState<any>(null);
  const [topics, setTopics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [m, mm, rm, tp] = await Promise.all([
        simApi.getModes(),
        simApi.comprehensiveMetrics(),
        simApi.recentMessages(),
        simApi.activeTopics(),
      ]);
      setModes(m);
      setMetrics(mm);
      setRecent(rm);
      setTopics(tp);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load modes", "bad");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    refresh().catch(() => {});
  }, [refresh]);

  const toggle = useCallback(
    async (modeType: string) => {
      try {
        const res = await simApi.toggleMode(modeType);
        toast.show(String((res as any)?.message ?? "Toggled"), (res as any)?.success === false ? "warn" : "ok");
        await refresh();
      } catch (e) {
        toast.show(e instanceof Error ? e.message : "Toggle failed", "bad");
      }
    },
    [refresh, toast]
  );

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="Vendor modes"
        subtitle="Kepware / Honeywell / Sparkplug B / Generic"
        actions={
          <Button type="button" onClick={() => refresh()} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <div className="muted" style={{ marginBottom: 10 }}>
          Uses <code>/api/modes*</code> endpoints (toggle, diagnostics, metrics, recent messages, topics).
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12 }}>
          {Array.isArray((modes as any)?.modes)
            ? (modes as any).modes.map((m: any) => (
                <div key={String(m?.mode_type ?? m?.name ?? "")} style={{ border: "1px solid var(--border-panel)", borderRadius: 2, padding: 12 }}>
                  <div className="section-title">{String(m?.display_name ?? m?.mode_type ?? m?.name ?? "mode")}</div>
                  <div className="muted" style={{ marginTop: 6 }}>
                    Status: {String(m?.enabled ?? m?.active ?? "unknown")}
                  </div>
                  <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <Button variant="primary" type="button" onClick={() => toggle(String(m?.mode_type ?? m?.name ?? ""))}>
                      Toggle
                    </Button>
                    <Button
                      type="button"
                      onClick={async () => {
                        try {
                          const d = await simApi.modeDiagnostics(String(m?.mode_type ?? m?.name ?? ""));
                          toast.show("Diagnostics loaded", "ok");
                          alert(JSON.stringify(d, null, 2));
                        } catch (e) {
                          toast.show(e instanceof Error ? e.message : "Diagnostics failed", "bad");
                        }
                      }}
                    >
                      Diagnostics
                    </Button>
                  </div>
                </div>
              ))
            : (
                <div className="muted">No mode list available yet.</div>
              )}
        </div>
      </Panel>

      <Panel title="Comprehensive metrics" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(metrics, null, 2)}</code>
        </pre>
      </Panel>

      <Panel title="Recent messages" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(recent, null, 2)}</code>
        </pre>
      </Panel>

      <Panel title="Active topics" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(topics, null, 2)}</code>
        </pre>
      </Panel>
    </div>
  );
}

