import { Button, Panel, StatusPill } from "@ot/ui-kit";
import { useCallback, useEffect, useState } from "react";
import { simApi } from "../api/simApi";
import type { ZeroBusStatusResponse } from "../api/types";
import { useAppToast } from "../toast/ToastContext";
import { useSimulatorWs } from "../ws/useSimulatorWs";

export function OverviewPage() {
  const toast = useAppToast();
  const ws = useSimulatorWs();
  const [health, setHealth] = useState<any>(null);
  const [zbStatus, setZbStatus] = useState<ZeroBusStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [h, z] = await Promise.all([simApi.getHealth(), simApi.zeroBusStatus()]);
      setHealth(h);
      setZbStatus(z);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to refresh", "bad");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    refresh().catch(() => {});
    const t = window.setInterval(() => refresh().catch(() => {}), 8000);
    return () => window.clearInterval(t);
  }, [refresh]);

  const zb = (zbStatus as any)?.status ?? {};
  const zbActive = (p: string) => Boolean(zb?.[p]?.active);
  const sim = (ws.status as any)?.simulators ?? {};
  const simRow = (p: string) => sim?.[p] ?? {};

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="Overview"
        subtitle="Health + high-level status"
        actions={
          <Button type="button" onClick={() => refresh()} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <StatusPill kind={health ? "ok" : "warn"}>Health: {health ? "ok" : "unknown"}</StatusPill>
          <StatusPill kind={zbStatus && (zbActive("opcua") || zbActive("mqtt") || zbActive("modbus")) ? "ok" : "warn"}>
            ZeroBus: {zbStatus ? (zbActive("opcua") || zbActive("mqtt") || zbActive("modbus") ? "active" : "idle") : "unknown"}
          </StatusPill>
          <StatusPill kind={ws.connected ? "ok" : "warn"}>WS: {ws.connected ? "connected" : "disconnected"}</StatusPill>
          <StatusPill kind={zbStatus ? (zbActive("opcua") ? "ok" : "warn") : "warn"}>OPC-UA stream: {zbStatus ? (zbActive("opcua") ? "on" : "off") : "?"}</StatusPill>
          <StatusPill kind={zbStatus ? (zbActive("mqtt") ? "ok" : "warn") : "warn"}>MQTT stream: {zbStatus ? (zbActive("mqtt") ? "on" : "off") : "?"}</StatusPill>
          <StatusPill kind={zbStatus ? (zbActive("modbus") ? "ok" : "warn") : "warn"}>Modbus stream: {zbStatus ? (zbActive("modbus") ? "on" : "off") : "?"}</StatusPill>
        </div>
        <div className="muted" style={{ marginTop: 10 }}>
          Start/stop protocol simulators is executed via WebSocket NLP commands (same contract as legacy).
        </div>
      </Panel>

      <Panel title="Protocol controls" subtitle="Start/stop via WebSocket (nlp_command)">
        {(["opcua", "mqtt", "modbus"] as const).map((p) => {
          const row = simRow(p);
          const running = Boolean(row?.running);
          return (
            <div key={p} style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", padding: "8px 0" }}>
              <div style={{ minWidth: 120, fontFamily: "var(--font-data)" }}>
                <strong>{p.toUpperCase()}</strong>
              </div>
              <StatusPill kind={running ? "ok" : "warn"}>{running ? "running" : "stopped"}</StatusPill>
              <span className="muted">sensors: {String(row?.sensor_count ?? "—")}</span>
              <span className="muted">updates: {String(row?.update_count ?? "—")}</span>
              <span className="muted">errors: {String(row?.errors ?? "—")}</span>
              <div style={{ display: "flex", gap: 10, marginLeft: "auto" }}>
                <Button
                  variant="primary"
                  type="button"
                  onClick={() => {
                    const ok = ws.startProtocol(p);
                    if (!ok) toast.show("WebSocket not connected", "warn");
                  }}
                  disabled={!ws.connected}
                >
                  Start
                </Button>
                <Button
                  variant="danger"
                  type="button"
                  onClick={() => {
                    const ok = ws.stopProtocol(p);
                    if (!ok) toast.show("WebSocket not connected", "warn");
                  }}
                  disabled={!ws.connected}
                >
                  Stop
                </Button>
              </div>
            </div>
          );
        })}
      </Panel>
    </div>
  );
}

