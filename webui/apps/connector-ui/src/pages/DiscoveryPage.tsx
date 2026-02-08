import { Button, Field, Panel, TextInput } from "@ot/ui-kit";
import { useCallback, useEffect, useMemo, useState } from "react";
import { connectorApi } from "../api/connectorApi";
import { useAuthState } from "../auth/AuthContext";
import { useNav } from "../nav/NavContext";
import { useAppToast } from "../toast/ToastContext";

export function DiscoveryPage() {
  const toast = useAppToast();
  const { can } = useAuthState();
  const nav = useNav();

  const [loading, setLoading] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);
  const [servers, setServers] = useState<any[]>([]);
  const [testResult, setTestResult] = useState<string>('Click "Test" on an endpoint to see detailed diagnostics here.');
  const [manualHost, setManualHost] = useState("");
  const [manualProtocol, setManualProtocol] = useState("opcua");
  const [manualPort, setManualPort] = useState("4840");

  const refresh = useCallback(async () => {
    if (!can.read) return;
    setLoading(true);
    try {
      const data = await connectorApi.getDiscovered();
      const list = Array.isArray((data as any)?.servers) ? (data as any).servers : Array.isArray(data) ? data : [];
      setServers(list);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load discovery results", "bad");
    } finally {
      setLoading(false);
    }
  }, [can.read, toast]);

  useEffect(() => {
    refresh().catch(() => {});
  }, [refresh]);

  const groups = useMemo(() => {
    const g: Record<string, any[]> = { opcua: [], mqtt: [], modbus: [], unknown: [] };
    for (const s of servers) {
      const p = (s?.protocol ?? s?.protocol_type ?? "unknown") as string;
      (g[p] ?? (g[p] = [])).push(s);
    }
    return g;
  }, [servers]);

  const scan = useCallback(async () => {
    if (!can.write) {
      toast.show("Requires write permission", "warn");
      return;
    }
    setScanLoading(true);
    try {
      await connectorApi.scanDiscovery();
      toast.show("Discovery scan started", "ok");
      // give scanner a beat
      setTimeout(() => refresh().catch(() => {}), 900);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to start scan", "bad");
    } finally {
      setScanLoading(false);
    }
  }, [can.write, refresh, toast]);

  const test = useCallback(
    async (s: any) => {
      if (!can.read) return;
      try {
        const res = await connectorApi.testDiscovery({
          protocol: String(s?.protocol ?? ""),
          host: String(s?.host ?? ""),
          port: Number(s?.port ?? 0),
        });
        setTestResult(JSON.stringify(res, null, 2));
        toast.show("Discovery test complete", "ok");
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Test failed";
        setTestResult(msg);
        toast.show(msg, "bad");
      }
    },
    [can.read, toast]
  );

  const manualTest = useCallback(async () => {
    if (!can.read) return;
    const portNum = Number(manualPort);
    if (!Number.isFinite(portNum) || portNum <= 0) {
      toast.show("Port must be a number", "bad");
      return;
    }
    try {
      const res = await connectorApi.testDiscovery({
        protocol: manualProtocol.trim(),
        host: manualHost.trim(),
        port: portNum,
      });
      setTestResult(JSON.stringify(res, null, 2));
      toast.show("Discovery test complete", "ok");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Test failed";
      setTestResult(msg);
      toast.show(msg, "bad");
    }
  }, [can.read, manualHost, manualPort, manualProtocol, toast]);

  const addAsSource = useCallback(
    (s: any) => {
      // Prefill payload for Sources form (mirrors legacy “Add as source” button)
      const payload = {
        name: `${String(s?.protocol ?? "source")}_${String(s?.host ?? "host").replaceAll(".", "_")}_${String(s?.port ?? "")}`,
        protocol: String(s?.protocol ?? ""),
        endpoint: String(s?.endpoint ?? ""),
        enabled: true,
      };
      window.localStorage.setItem("connector-ui.sourcePrefill", JSON.stringify(payload));
      toast.show("Prefilled source. Opening Sources…", "ok");
      nav.go("sources");
    },
    [nav, toast]
  );

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="Discovery"
        subtitle="Find protocol servers (OPC-UA, MQTT, Modbus)"
        actions={
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
            <Button type="button" onClick={() => refresh()} disabled={loading || !can.read}>
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
            <Button variant="primary" type="button" onClick={() => scan()} disabled={scanLoading || !can.write}>
              {scanLoading ? "Scanning..." : "Scan"}
            </Button>
          </div>
        }
      >
        <div className="muted">
          Calls <code>POST /api/discovery/scan</code> and renders <code>GET /api/discovery/servers</code>.
        </div>
      </Panel>

      <Panel title="Discovered endpoints" subtitle="Add as source or test connectivity">
        {(["opcua", "mqtt", "modbus"] as const).map((proto) => (
          <div key={proto} style={{ marginBottom: 14 }}>
            <div className="section-title" style={{ marginBottom: 8 }}>
              {proto.toUpperCase()} <span className="muted">({groups[proto]?.length ?? 0} found)</span>
            </div>
            <div style={{ border: "1px solid var(--border-panel)", borderRadius: 2, overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-data)", fontSize: 12 }}>
                <thead>
                  <tr style={{ background: "rgba(0,0,0,0.35)" }}>
                    <th style={{ textAlign: "left", padding: 8 }}>Host</th>
                    <th style={{ textAlign: "left", padding: 8 }}>Port</th>
                    <th style={{ textAlign: "left", padding: 8 }}>Endpoint</th>
                    <th style={{ textAlign: "left", padding: 8 }}>Reachable</th>
                    <th style={{ textAlign: "left", padding: 8 }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(groups[proto] ?? []).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="muted" style={{ padding: 10 }}>
                        None discovered yet. Click “Scan”.
                      </td>
                    </tr>
                  ) : (
                    (groups[proto] ?? []).map((s, idx) => (
                      <tr key={`${proto}-${idx}`} style={{ borderTop: "1px solid rgba(255,255,255,0.03)" }}>
                        <td style={{ padding: 8 }}>
                          <code>{String(s?.host ?? "")}</code>
                        </td>
                        <td style={{ padding: 8 }}>{String(s?.port ?? "")}</td>
                        <td style={{ padding: 8 }}>
                          <code>{String(s?.endpoint ?? "")}</code>
                        </td>
                        <td style={{ padding: 8 }}>
                          {s?.reachable === true ? "yes" : s?.reachable === false ? "no" : <span className="muted">n/a</span>}
                        </td>
                        <td style={{ padding: 8 }}>
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            <Button type="button" onClick={() => test(s)} disabled={!can.read}>
                              Test
                            </Button>
                            <Button variant="primary" type="button" onClick={() => addAsSource(s)} disabled={!can.write}>
                              Add as source
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </Panel>

      <Panel title="Test connection" subtitle="Validate a discovered or manual endpoint">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 160px", gap: 10 }}>
          <Field label="Host">
            <TextInput value={manualHost} onChange={(e) => setManualHost(e.target.value)} placeholder="127.0.0.1" />
          </Field>
          <Field label="Protocol">
            <TextInput value={manualProtocol} onChange={(e) => setManualProtocol(e.target.value)} placeholder="opcua | mqtt | modbus" />
          </Field>
          <Field label="Port">
            <TextInput value={manualPort} onChange={(e) => setManualPort(e.target.value)} placeholder="4840" />
          </Field>
        </div>
        <div style={{ marginTop: 10, display: "flex", gap: 10 }}>
          <Button type="button" onClick={() => manualTest()} disabled={!can.read}>
            Test
          </Button>
        </div>
        <div className="muted" style={{ marginTop: 10 }}>
          Uses <code>POST /api/discovery/test</code>.
        </div>
      </Panel>

      <Panel title="Discovery test result" subtitle="Detailed output">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{testResult}</code>
        </pre>
      </Panel>
    </div>
  );
}

