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
  const [pendingProtocolAction, setPendingProtocolAction] = useState<Partial<Record<"opcua" | "mqtt" | "modbus", "start" | "stop">>>({});

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

  const requestProtocolAction = useCallback(
    (protocol: "opcua" | "mqtt" | "modbus", action: "start" | "stop") => {
      if (!ws.connected) {
        toast.show("WebSocket not connected", "warn");
        return;
      }
      const ok = action === "start" ? ws.startProtocol(protocol) : ws.stopProtocol(protocol);
      if (!ok) {
        toast.show("WebSocket not connected", "warn");
        return;
      }

      setPendingProtocolAction((prev) => ({ ...prev, [protocol]: action }));
      toast.show(`${action === "start" ? "Start" : "Stop"} requested for ${protocol.toUpperCase()}`, "ok");
      // Force immediate and short-lived follow-up status refresh attempts.
      ws.getStatus();
      window.setTimeout(() => ws.getStatus(), 250);
      window.setTimeout(() => ws.getStatus(), 800);
      window.setTimeout(() => ws.getStatus(), 1500);
      window.setTimeout(() => ws.getStatus(), 3000);
      window.setTimeout(() => ws.getStatus(), 5000);
      window.setTimeout(() => {
        setPendingProtocolAction((prev) => {
          if (prev[protocol] !== action) return prev;
          toast.show(
            `${protocol.toUpperCase()} is still ${
              action === "start" ? "starting" : "stopping"
            }. Check protocol logs if this persists.`,
            "warn"
          );
          const next = { ...prev };
          delete next[protocol];
          return next;
        });
      }, 8000);
    },
    [toast, ws]
  );

  useEffect(() => {
    setPendingProtocolAction((prev) => {
      let changed = false;
      const next = { ...prev };
      (["opcua", "mqtt", "modbus"] as const).forEach((protocol) => {
        const pending = prev[protocol];
        if (!pending) return;
        const running = Boolean(simRow(protocol)?.running);
        if ((pending === "start" && running) || (pending === "stop" && !running)) {
          delete next[protocol];
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [ws.status]);

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
          const pending = pendingProtocolAction[p];
          const stateLabel = pending === "start" ? "starting" : pending === "stop" ? "stopping" : running ? "running" : "stopped";
          const stateKind = pending ? "warn" : running ? "ok" : "warn";
          return (
            <div key={p} style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", padding: "8px 0" }}>
              <div style={{ minWidth: 120, fontFamily: "var(--font-data)" }}>
                <strong>{p.toUpperCase()}</strong>
              </div>
              <StatusPill kind={stateKind}>{stateLabel}</StatusPill>
              <span className="muted">sensors: {String(row?.sensor_count ?? "—")}</span>
              <span className="muted">updates: {String(row?.update_count ?? "—")}</span>
              <span className="muted">errors: {String(row?.errors ?? "—")}</span>
              <div style={{ display: "flex", gap: 10, marginLeft: "auto" }}>
                <Button
                  variant="primary"
                  type="button"
                  onClick={() => requestProtocolAction(p, "start")}
                  disabled={!ws.connected || pending === "start" || running}
                >
                  {pending === "start" ? "Starting..." : "Start"}
                </Button>
                <Button
                  variant="danger"
                  type="button"
                  onClick={() => requestProtocolAction(p, "stop")}
                  disabled={!ws.connected || pending === "stop" || !running}
                >
                  {pending === "stop" ? "Stopping..." : "Stop"}
                </Button>
              </div>
            </div>
          );
        })}
      </Panel>
    </div>
  );
}

