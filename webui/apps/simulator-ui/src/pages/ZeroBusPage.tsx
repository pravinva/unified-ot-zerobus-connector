import { Button, Field, Panel, Select, TextInput } from "@ot/ui-kit";
import { useCallback, useEffect, useMemo, useState } from "react";
import { simApi } from "../api/simApi";
import type { Protocol, SensorsResponse, ZeroBusStatusResponse } from "../api/types";
import { useAppToast } from "../toast/ToastContext";

type SensorItem = {
  path: string;
  name: string;
  type: string;
  industryDisplay: string;
  plc: string;
};

export function ZeroBusPage() {
  const toast = useAppToast();
  const [protocol, setProtocol] = useState<Protocol>("opcua");
  const [status, setStatus] = useState<ZeroBusStatusResponse | null>(null);
  const [cfgLoading, setCfgLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [sensorLoading, setSensorLoading] = useState(false);
  const [config, setConfig] = useState<any>({});
  const [sensorsByIndustry, setSensorsByIndustry] = useState<SensorsResponse | null>(null);
  const [selectedSensors, setSelectedSensors] = useState<Set<string>>(new Set());
  const [industryFilters, setIndustryFilters] = useState<Set<string>>(new Set());
  const [plcFilters, setPlcFilters] = useState<Set<string>>(new Set());
  const [lastResult, setLastResult] = useState<string>("");

  function parseFqn(fqn: string): { catalog: string; schema: string; table: string } | null {
    const parts = (fqn || "")
      .split(".")
      .map((p) => p.trim())
      .filter(Boolean);
    if (parts.length !== 3) return null;
    return { catalog: parts[0], schema: parts[1], table: parts[2] };
  }

  const tableFqn = useMemo(() => {
    const t = config?.target ?? {};
    const c = String(t?.catalog ?? "");
    const s = String(t?.schema ?? "");
    const tb = String(t?.table ?? "");
    return [c, s, tb].filter(Boolean).join(".");
  }, [config]);

  const setTableFqn = useCallback(
    (fqn: string) => {
      const parsed = parseFqn(fqn);
      if (!parsed) return;
      setConfig((c: any) => ({ ...c, target: { ...(c?.target ?? {}), ...parsed } }));
    },
    []
  );

  const refreshStatus = useCallback(async () => {
    try {
      setStatus(await simApi.zeroBusStatus());
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load status", "bad");
    }
  }, [toast]);

  const loadSensors = useCallback(async () => {
    setSensorLoading(true);
    try {
      const sensors = await simApi.getSensors();
      setSensorsByIndustry(sensors);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load sensors", "bad");
    } finally {
      setSensorLoading(false);
    }
  }, [toast]);

  const loadConfig = useCallback(async () => {
    setCfgLoading(true);
    try {
      const res = await simApi.loadZeroBusConfig(protocol);
      if ((res as any)?.success) {
        setConfig((res as any).config ?? {});
        const loadedSelected = Array.isArray((res as any)?.config?.selected_sensors)
          ? (res as any).config.selected_sensors
          : [];
        setSelectedSensors(new Set(loadedSelected));
        setLastResult("Loaded saved config");
        toast.show("Loaded saved config", "ok");
      } else {
        setLastResult(String((res as any)?.message ?? "No saved config"));
        toast.show(String((res as any)?.message ?? "No saved config"), "warn");
      }
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load config", "bad");
    } finally {
      setCfgLoading(false);
    }
  }, [protocol, toast]);

  useEffect(() => {
    refreshStatus().catch(() => {});
    loadSensors().catch(() => {});
    loadConfig().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [protocol]);

  useEffect(() => {
    setConfig((c: any) => ({ ...c, selected_sensors: Array.from(selectedSensors) }));
  }, [selectedSensors]);

  const allSensors = useMemo<SensorItem[]>(() => {
    if (!sensorsByIndustry) return [];
    const flat: SensorItem[] = [];
    for (const industry of Object.values(sensorsByIndustry)) {
      const industryDisplay = String(industry.display_name ?? industry.name ?? "Unknown");
      for (const sensor of industry.sensors ?? []) {
        const plcVendor = String((sensor as any).plc_vendor ?? "").trim();
        const plcModel = String((sensor as any).plc_model ?? "").trim();
        const plc = `${plcVendor} ${plcModel}`.trim() || "Unknown PLC";
        flat.push({
          path: String((sensor as any).path ?? ""),
          name: String((sensor as any).name ?? ""),
          type: String((sensor as any).type ?? "unknown"),
          industryDisplay,
          plc,
        });
      }
    }
    return flat.filter((s) => s.path.length > 0);
  }, [sensorsByIndustry]);

  const industryOptions = useMemo(() => {
    return Array.from(new Set(allSensors.map((s) => s.industryDisplay))).sort((a, b) => a.localeCompare(b));
  }, [allSensors]);

  const plcOptions = useMemo(() => {
    return Array.from(new Set(allSensors.map((s) => s.plc))).sort((a, b) => a.localeCompare(b));
  }, [allSensors]);

  const filteredSensors = useMemo(() => {
    return allSensors.filter((sensor) => {
      if (industryFilters.size > 0 && !industryFilters.has(sensor.industryDisplay)) return false;
      if (plcFilters.size > 0 && !plcFilters.has(sensor.plc)) return false;
      return true;
    });
  }, [allSensors, industryFilters, plcFilters]);

  const toggleIndustryFilter = useCallback((industry: string, checked: boolean) => {
    setIndustryFilters((prev) => {
      const next = new Set(prev);
      if (checked) next.add(industry);
      else next.delete(industry);
      return next;
    });
  }, []);

  const togglePlcFilter = useCallback((plc: string, checked: boolean) => {
    setPlcFilters((prev) => {
      const next = new Set(prev);
      if (checked) next.add(plc);
      else next.delete(plc);
      return next;
    });
  }, []);

  const toggleSensorSelection = useCallback((path: string, checked: boolean) => {
    setSelectedSensors((prev) => {
      const next = new Set(prev);
      if (checked) next.add(path);
      else next.delete(path);
      return next;
    });
  }, []);

  const selectFilteredSensors = useCallback(() => {
    setSelectedSensors((prev) => {
      const next = new Set(prev);
      for (const sensor of filteredSensors) next.add(sensor.path);
      return next;
    });
  }, [filteredSensors]);

  const clearFilteredSensors = useCallback(() => {
    setSelectedSensors((prev) => {
      const next = new Set(prev);
      for (const sensor of filteredSensors) next.delete(sensor.path);
      return next;
    });
  }, [filteredSensors]);

  const save = useCallback(async () => {
    setActionLoading(true);
    try {
      const res = await simApi.saveZeroBusConfig(protocol, config);
      setLastResult(JSON.stringify(res, null, 2));
      toast.show(String((res as any)?.message ?? "Saved"), (res as any)?.success === false ? "warn" : "ok");
      await refreshStatus();
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Save failed", "bad");
    } finally {
      setActionLoading(false);
    }
  }, [config, protocol, refreshStatus, toast]);

  const test = useCallback(async () => {
    setActionLoading(true);
    try {
      const res = await simApi.testZeroBus(protocol, config);
      setLastResult(JSON.stringify(res, null, 2));
      toast.show(String((res as any)?.message ?? "Test complete"), (res as any)?.success === false ? "warn" : "ok");
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Test failed", "bad");
    } finally {
      setActionLoading(false);
    }
  }, [config, protocol, toast]);

  const start = useCallback(async () => {
    setActionLoading(true);
    try {
      const res = await simApi.startZeroBus(protocol);
      setLastResult(JSON.stringify(res, null, 2));
      toast.show(String((res as any)?.message ?? "Start requested"), (res as any)?.success === false ? "warn" : "ok");
      await refreshStatus();
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Start failed", "bad");
    } finally {
      setActionLoading(false);
    }
  }, [protocol, refreshStatus, toast]);

  const stop = useCallback(async () => {
    setActionLoading(true);
    try {
      const res = await simApi.stopZeroBus(protocol);
      setLastResult(JSON.stringify(res, null, 2));
      toast.show(String((res as any)?.message ?? "Stop requested"), (res as any)?.success === false ? "warn" : "ok");
      await refreshStatus();
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Stop failed", "bad");
    } finally {
      setActionLoading(false);
    }
  }, [protocol, refreshStatus, toast]);

  const hasConfig = Boolean((status as any)?.status?.[protocol]?.has_config);
  const active = Boolean((status as any)?.status?.[protocol]?.active);

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="ZeroBus"
        subtitle="Per-protocol configuration + start/stop/test"
        actions={
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Button type="button" onClick={() => refreshStatus()} disabled={cfgLoading || actionLoading}>
              Refresh status
            </Button>
            <Button type="button" onClick={() => loadConfig()} disabled={cfgLoading}>
              {cfgLoading ? "Loading..." : "Load saved"}
            </Button>
            <Button variant="primary" type="button" onClick={() => save()} disabled={actionLoading}>
              Save
            </Button>
            <Button type="button" onClick={() => test()} disabled={actionLoading}>
              Test
            </Button>
            <Button variant="primary" type="button" onClick={() => start()} disabled={actionLoading || !hasConfig}>
              Start streaming
            </Button>
            <Button variant="danger" type="button" onClick={() => stop()} disabled={actionLoading || !active}>
              Stop streaming
            </Button>
          </div>
        }
      >
        <div style={{ display: "grid", gap: 10 }}>
          <Field label="Protocol">
            <Select value={protocol} onChange={(e) => setProtocol(e.target.value as Protocol)}>
              <option value="opcua">OPC-UA</option>
              <option value="mqtt">MQTT</option>
              <option value="modbus">Modbus</option>
            </Select>
          </Field>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Workspace host">
              <TextInput
                value={String(config?.workspace_host ?? "")}
                onChange={(e) => setConfig((c: any) => ({ ...c, workspace_host: e.target.value }))}
                placeholder="https://adb-..."
              />
            </Field>
            <Field label="ZeroBus endpoint">
              <TextInput
                value={String(config?.zerobus_endpoint ?? "")}
                onChange={(e) => setConfig((c: any) => ({ ...c, zerobus_endpoint: e.target.value }))}
                placeholder="<workspaceId>.zerobus.<region>.cloud.databricks.com"
              />
            </Field>
          </div>

          <Field label="Target table (catalog.schema.table)">
            <TextInput
              value={tableFqn}
              onChange={(e) => {
                const v = e.target.value;
                // allow partial typing without clobbering
                setConfig((c: any) => ({ ...c, __table_fqn_draft: v }));
                const parsed = parseFqn(v);
                if (parsed) setTableFqn(v);
              }}
              placeholder="main.iot_data.sensor_readings"
            />
          </Field>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Client ID">
              <TextInput
                value={String(config?.auth?.client_id ?? "")}
                onChange={(e) => setConfig((c: any) => ({ ...c, auth: { ...(c?.auth ?? {}), client_id: e.target.value } }))}
              />
            </Field>
            <Field label="Client secret">
              <TextInput
                type="password"
                value={String(config?.auth?.client_secret ?? "")}
                onChange={(e) => setConfig((c: any) => ({ ...c, auth: { ...(c?.auth ?? {}), client_secret: e.target.value } }))}
              />
            </Field>
          </div>

          <div style={{ border: "1px solid var(--border-panel)", borderRadius: 2, padding: 12, display: "grid", gap: 10 }}>
            <div className="section-title">Sensor selection for ZeroBus</div>
            <div className="muted">
              Selected: <strong>{selectedSensors.size}</strong> / {allSensors.length} sensors
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div style={{ display: "grid", gap: 6 }}>
                <div className="muted" style={{ fontWeight: 600 }}>Filter by Industry</div>
                <div style={{ maxHeight: 140, overflow: "auto", border: "1px solid var(--border-panel)", borderRadius: 2, padding: 8 }}>
                  {industryOptions.map((industry) => (
                    <label key={industry} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                      <input
                        type="checkbox"
                        checked={industryFilters.has(industry)}
                        onChange={(e) => toggleIndustryFilter(industry, e.target.checked)}
                      />
                      <span>{industry}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: "grid", gap: 6 }}>
                <div className="muted" style={{ fontWeight: 600 }}>Filter by PLC/System</div>
                <div style={{ maxHeight: 140, overflow: "auto", border: "1px solid var(--border-panel)", borderRadius: 2, padding: 8 }}>
                  {plcOptions.map((plc) => (
                    <label key={plc} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                      <input type="checkbox" checked={plcFilters.has(plc)} onChange={(e) => togglePlcFilter(plc, e.target.checked)} />
                      <span>{plc}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <Button type="button" onClick={() => selectFilteredSensors()}>
                Select filtered ({filteredSensors.length})
              </Button>
              <Button type="button" onClick={() => clearFilteredSensors()}>
                Clear filtered
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setIndustryFilters(new Set());
                  setPlcFilters(new Set());
                }}
              >
                Clear filters
              </Button>
            </div>

            <div style={{ maxHeight: 260, overflow: "auto", border: "1px solid var(--border-panel)", borderRadius: 2, padding: 8 }}>
              {sensorLoading ? (
                <div className="muted">Loading sensors...</div>
              ) : filteredSensors.length === 0 ? (
                <div className="muted">No sensors match current filters.</div>
              ) : (
                filteredSensors.map((sensor) => (
                  <label key={sensor.path} style={{ display: "grid", gridTemplateColumns: "20px 1fr", gap: 8, marginBottom: 8 }}>
                    <input
                      type="checkbox"
                      checked={selectedSensors.has(sensor.path)}
                      onChange={(e) => toggleSensorSelection(sensor.path, e.target.checked)}
                    />
                    <span>
                      <strong>{sensor.name}</strong>
                      <span className="muted"> - {sensor.industryDisplay} - {sensor.plc}</span>
                    </span>
                  </label>
                ))
              )}
            </div>
          </div>

          <div className="muted">
            Status: {active ? "streaming active" : "inactive"}; saved config: {hasConfig ? "yes" : "no"}
          </div>
        </div>
      </Panel>

      <Panel title="Last result" subtitle="Raw response">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{lastResult || "—"}</code>
        </pre>
      </Panel>
    </div>
  );
}

