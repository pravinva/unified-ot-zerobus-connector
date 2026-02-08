import { Button, Field, Panel, Select, StatusPill, TextInput } from "@ot/ui-kit";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { simApi } from "../api/simApi";
import type { IndustriesResponse, SensorsResponse } from "../api/types";
import { OverlayChart } from "../components/OverlayChart";
import { useAppToast } from "../toast/ToastContext";
import { useSimulatorWs } from "../ws/useSimulatorWs";

export function SensorsPage() {
  const toast = useAppToast();
  const ws = useSimulatorWs();
  const [industries, setIndustries] = useState<IndustriesResponse>([]);
  const [sensorsByIndustry, setSensorsByIndustry] = useState<SensorsResponse>({});
  const [industry, setIndustry] = useState<string>("all");
  const [search, setSearch] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);

  // time-series history per sensor
  const historyRef = useRef<Map<string, number[]>>(new Map());
  const [tick, setTick] = useState(0); // force chart updates on new points
  const maxPoints = 240;

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [i, s] = await Promise.all([simApi.getIndustries(), simApi.getSensors()]);
      setIndustries(i);
      setSensorsByIndustry(s);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load sensors", "bad");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    refresh().catch(() => {});
  }, [refresh]);

  const flatSensors = useMemo(() => {
    const items: Array<{
      industry: string;
      sensor: {
        path: string;
        name: string;
        type?: string;
        unit?: string;
        min_value?: number;
        max_value?: number;
        plc_vendor?: string;
        plc_model?: string;
        protocols?: string[];
      };
    }> = [];
    for (const [ind, v] of Object.entries(sensorsByIndustry ?? {})) {
      const list = Array.isArray(v?.sensors) ? v.sensors : [];
      for (const s of list) items.push({ industry: ind, sensor: s as any });
    }
    return items;
  }, [sensorsByIndustry]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return flatSensors.filter((it) => {
      if (industry !== "all" && it.industry !== industry) return false;
      if (!q) return true;
      const hay = `${it.sensor.path} ${it.sensor.name} ${it.sensor.type ?? ""} ${it.sensor.unit ?? ""} ${it.sensor.plc_vendor ?? ""} ${
        it.sensor.plc_model ?? ""
      }`.toLowerCase();
      return hay.includes(q);
    });
  }, [flatSensors, industry, search]);

  // Subscribe/unsubscribe when selection changes.
  useEffect(() => {
    if (!ws.connected) return;
    ws.subscribe(selected);
    // keep it simple: when selection shrinks, unsubscribe those removed
    return () => {};
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ws.connected, selected.join("|")]);

  // Append WS values into history for selected sensors.
  useEffect(() => {
    const sensors = ws.sensorData as Record<string, unknown>;
    if (!sensors || typeof sensors !== "object") return;
    let appended = false;
    for (const path of selected) {
      const v = sensors[path];
      if (typeof v !== "number" || !Number.isFinite(v)) continue;
      const arr = historyRef.current.get(path) ?? [];
      arr.push(v);
      if (arr.length > maxPoints) arr.splice(0, arr.length - maxPoints);
      historyRef.current.set(path, arr);
      appended = true;
    }
    if (appended) setTick((t) => t + 1);
  }, [selected, ws.sensorData]);

  const selectedMeta = useMemo(() => {
    const byPath = new Map<string, { label: string; unit?: string }>();
    for (const it of flatSensors) {
      byPath.set(it.sensor.path, { label: it.sensor.path, unit: it.sensor.unit });
    }
    return byPath;
  }, [flatSensors]);

  const series = useMemo(() => {
    // tick used to update when historyRef changes
    void tick;
    return selected.map((path) => {
      const meta = selectedMeta.get(path);
      return {
        key: path,
        label: meta?.unit ? `${path} (${meta.unit})` : path,
        values: historyRef.current.get(path) ?? [],
      };
    });
  }, [selected, selectedMeta, tick]);

  const addSensor = (path: string) => {
    setSelected((prev) => (prev.includes(path) ? prev : [...prev, path].slice(0, 8)));
  };

  const removeSensor = (path: string) => {
    setSelected((prev) => prev.filter((p) => p !== path));
    historyRef.current.delete(path);
    ws.unsubscribe([path]);
  };

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel title="Sensor overlay" subtitle="Pick sensors and overlay live charts">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <StatusPill kind={ws.connected ? "ok" : "warn"}>WS: {ws.connected ? "connected" : "disconnected"}</StatusPill>
          <StatusPill kind={selected.length ? "ok" : "warn"}>Selected: {selected.length}/8</StatusPill>
          <div className="muted">Live values come from WebSocket subscriptions (same contract as legacy).</div>
        </div>

        <div style={{ marginTop: 12 }}>
          <OverlayChart series={series} height={260} maxPoints={maxPoints} />
        </div>

        {selected.length > 0 ? (
          <div style={{ marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
            {selected.map((p) => (
              <Button key={p} variant="danger" type="button" onClick={() => removeSensor(p)}>
                Remove {p}
              </Button>
            ))}
          </div>
        ) : (
          <div className="muted" style={{ marginTop: 12 }}>
            Select sensors below to start streaming and plotting.
          </div>
        )}
      </Panel>

      <Panel
        title="Sensors"
        subtitle="Browse and add to overlay"
        actions={
          <Button type="button" onClick={() => refresh()} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <Field label="Industry">
            <Select value={industry} onChange={(e) => setIndustry(e.target.value)}>
              <option value="all">All industries</option>
              {industries.map((i) => (
                <option key={i.name} value={i.name}>
                  {i.name} ({i.sensor_count})
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Search">
            <TextInput value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Filter by name/path/type/unit/plc…" />
          </Field>
        </div>

        <div className="muted" style={{ marginTop: 10 }}>
          Showing {filtered.length} sensors. Click “Add” to overlay (max 8).
        </div>

        <div style={{ marginTop: 10, border: "1px solid var(--border-panel)", borderRadius: 2, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-data)", fontSize: 12 }}>
            <thead>
              <tr style={{ background: "rgba(0,0,0,0.35)" }}>
                <th style={{ textAlign: "left", padding: 8, width: 110 }}>Industry</th>
                <th style={{ textAlign: "left", padding: 8 }}>Path</th>
                <th style={{ textAlign: "left", padding: 8, width: 120 }}>Type</th>
                <th style={{ textAlign: "left", padding: 8, width: 90 }}>Unit</th>
                <th style={{ textAlign: "left", padding: 8, width: 180 }}>PLC</th>
                <th style={{ textAlign: "right", padding: 8, width: 120 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 250).map((it) => {
                const path = it.sensor.path;
                const plc = [it.sensor.plc_vendor, it.sensor.plc_model].filter(Boolean).join(" ");
                const already = selected.includes(path);
                return (
                  <tr key={path} style={{ borderTop: "1px solid rgba(255,255,255,0.03)" }}>
                    <td style={{ padding: 8, color: "var(--text-secondary)" }}>{it.industry}</td>
                    <td style={{ padding: 8, color: "var(--text-accent)" }}>{path}</td>
                    <td style={{ padding: 8 }}>{it.sensor.type ?? "—"}</td>
                    <td style={{ padding: 8 }}>{it.sensor.unit ?? "—"}</td>
                    <td style={{ padding: 8, color: "var(--text-secondary)" }}>{plc || "—"}</td>
                    <td style={{ padding: 8, textAlign: "right" }}>
                      <Button type="button" variant={already ? "secondary" : "primary"} disabled={already || selected.length >= 8} onClick={() => addSensor(path)}>
                        {already ? "Added" : "Add"}
                      </Button>
                    </td>
                  </tr>
                );
              })}
              {filtered.length > 250 && (
                <tr>
                  <td colSpan={6} className="muted" style={{ padding: 10 }}>
                    Showing first 250 results. Narrow your filter to see more.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

