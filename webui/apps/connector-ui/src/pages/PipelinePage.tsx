import { Button, Field, Panel, Select, StatusPill } from "@ot/ui-kit";
import { useCallback, useEffect, useMemo, useState } from "react";
import { connectorApi } from "../api/connectorApi";
import type { ConnectorMetrics, PipelineDiagnostics } from "../api/types";
import { useAuthState } from "../auth/AuthContext";
import { useAppToast } from "../toast/ToastContext";

type StageSample = Record<string, unknown>;
type StageView = { name: string; description?: string; samples: StageSample[] };
type ProtocolVendorPipeline = { protocol: string; vendor: string; recordCount: number; stages: StageView[] };

const PROTOCOL_DISPLAY: Record<string, string> = {
  opcua: "OPC UA",
  mqtt: "MQTT",
  modbus: "Modbus",
  unknown: "Unknown",
};

const VENDOR_DISPLAY: Record<string, string> = {
  kepware: "Kepware",
  sparkplug_b: "Sparkplug B",
  honeywell: "Honeywell",
  opcua: "OPC UA",
  modbus: "Modbus",
  generic: "Generic",
  unknown: "Unknown",
};

const STAGE_DISPLAY: Record<string, string> = {
  raw_protocol: "Raw Protocol",
  after_vendor_detection: "Vendor Detection",
  after_normalization: "ISA-95 Normalization",
  zerobus_batch: "ZeroBus Batch",
};

function organizeByProtocolVendor(vendorPipelines: any): Record<string, ProtocolVendorPipeline> {
  const out: Record<string, ProtocolVendorPipeline> = {};

  for (const [vendorKey, vendorData] of Object.entries(vendorPipelines ?? {})) {
    const stages: any[] = (vendorData as any)?.pipeline_stages || [];
    if (!Array.isArray(stages) || stages.length === 0) continue;

    // Map source_name -> protocol (from first stage samples)
    const sourceNameToProtocol: Record<string, string> = {};
    const firstSamples: any[] = stages[0]?.samples || [];
    for (const s of firstSamples) {
      const proto = String(s?.protocol ?? s?.protocol_type ?? "unknown");
      const sn = String(s?.source_name ?? "unknown");
      sourceNameToProtocol[sn] = proto;
    }

    // Group samples by protocol per stage
    const protocolKeys = new Set(Object.values(sourceNameToProtocol));
    if (protocolKeys.size === 0) protocolKeys.add("unknown");

    const perProtocol: Record<string, { stages: StageView[]; recordCount: number }> = {};
    for (const p of protocolKeys) perProtocol[p] = { stages: [], recordCount: 0 };

    for (let i = 0; i < stages.length; i++) {
      const stage = stages[i] || {};
      const stageName = String(stage?.stage ?? stage?.name ?? stage?.stage_name ?? `Stage ${i + 1}`);
      const stageDesc = typeof stage?.description === "string" ? stage.description : "";
      const samples: any[] = stage?.samples || [];

      // init
      for (const p of Object.keys(perProtocol)) {
        perProtocol[p].stages[i] = perProtocol[p].stages[i] || { name: stageName, description: stageDesc, samples: [] };
      }

      for (const s of samples) {
        let proto = s?.protocol ?? s?.protocol_type;
        if (!proto && s?.source_name) proto = sourceNameToProtocol[String(s.source_name)];
        proto = String(proto ?? "unknown");
        if (!perProtocol[proto]) {
          perProtocol[proto] = { stages: Array.from({ length: stages.length }, (_, idx) => ({ name: idx === i ? stageName : `Stage ${idx + 1}`, samples: [] })), recordCount: 0 };
        }
        perProtocol[proto].stages[i] = perProtocol[proto].stages[i] || { name: stageName, description: stageDesc, samples: [] };
        perProtocol[proto].stages[i].samples.push(s);
        perProtocol[proto].recordCount++;
      }
    }

    for (const [proto, pv] of Object.entries(perProtocol)) {
      const key = `${proto}__${vendorKey}`;
      out[key] = { protocol: proto, vendor: vendorKey, recordCount: pv.recordCount, stages: pv.stages.filter(Boolean) };
    }
  }

  return out;
}

export function PipelinePage() {
  const toast = useAppToast();
  const { can } = useAuthState();
  const [loading, setLoading] = useState(false);

  const [pipeline, setPipeline] = useState<PipelineDiagnostics | null>(null);
  const [metrics, setMetrics] = useState<ConnectorMetrics | null>(null);

  const [filterProtocol, setFilterProtocol] = useState<string>("all");
  const [filterVendor, setFilterVendor] = useState<string>("all");
  const [showRawBreakdown, setShowRawBreakdown] = useState(false);

  const refresh = useCallback(async () => {
    if (!can.read) return;
    setLoading(true);
    try {
      const [p, m] = await Promise.all([connectorApi.getPipelineDiagnostics(), connectorApi.getMetrics()]);
      setPipeline(p);
      setMetrics(m);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load pipeline diagnostics", "bad");
    } finally {
      setLoading(false);
    }
  }, [can.read, toast]);

  useEffect(() => {
    refresh().catch(() => {});
    const t = window.setInterval(() => refresh().catch(() => {}), 7000);
    return () => window.clearInterval(t);
  }, [refresh]);

  const vendorFormats = (pipeline as any)?.vendor_format_summary || {};
  const normalizationEnabled = Boolean((pipeline as any)?.normalization_enabled ?? false);

  const protocolVendorPipelines = useMemo(() => organizeByProtocolVendor((pipeline as any)?.vendor_pipelines || {}), [pipeline]);
  const protocols = useMemo(() => Array.from(new Set(Object.values(protocolVendorPipelines).map((v) => v.protocol))).sort(), [protocolVendorPipelines]);
  const vendors = useMemo(() => Array.from(new Set(Object.values(protocolVendorPipelines).map((v) => v.vendor))).sort(), [protocolVendorPipelines]);

  const filtered = useMemo(() => {
    return Object.entries(protocolVendorPipelines).filter(([, v]) => {
      if (filterProtocol !== "all" && v.protocol !== filterProtocol) return false;
      if (filterVendor !== "all" && v.vendor !== filterVendor) return false;
      return true;
    });
  }, [filterProtocol, filterVendor, protocolVendorPipelines]);

  const breakdown = (metrics as any)?.bridge?.protocol_vendor_breakdown || {};

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="Pipeline diagnostics"
        subtitle="Raw Protocol → Vendor Detection → ISA-95 → ZeroBus (samples + normalization status)"
        actions={
          <Button type="button" onClick={() => refresh()} disabled={loading || !can.read}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <StatusPill kind="ok">Kepware: {vendorFormats.kepware || 0}</StatusPill>
          <StatusPill kind="ok">Sparkplug B: {vendorFormats.sparkplug_b || 0}</StatusPill>
          <StatusPill kind="ok">Honeywell: {vendorFormats.honeywell || 0}</StatusPill>
          <StatusPill kind="ok">Generic: {vendorFormats.generic || 0}</StatusPill>
          <StatusPill kind={normalizationEnabled ? "ok" : "warn"}>
            ISA-95 normalization: {normalizationEnabled ? "ENABLED" : "DISABLED"}
          </StatusPill>
        </div>

        <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <Field label="Protocol filter">
            <Select value={filterProtocol} onChange={(e) => setFilterProtocol(e.target.value)}>
              <option value="all">All protocols</option>
              {protocols.filter((p) => p !== "unknown").map((p) => (
                <option key={p} value={p}>
                  {PROTOCOL_DISPLAY[p] ?? p}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Vendor format filter">
            <Select value={filterVendor} onChange={(e) => setFilterVendor(e.target.value)}>
              <option value="all">All vendors</option>
              {vendors.filter((v) => v !== "unknown").map((v) => (
                <option key={v} value={v}>
                  {VENDOR_DISPLAY[v] ?? v}
                </option>
              ))}
            </Select>
          </Field>
        </div>

        <div className="muted" style={{ marginTop: 10 }}>
          Data: <code>/api/diagnostics/pipeline</code> + <code>/api/metrics</code>.
        </div>
      </Panel>

      <Panel
        title="Protocol → vendor breakdown"
        subtitle="What the bridge is detecting (counts)"
        actions={
          <Button type="button" variant="secondary" onClick={() => setShowRawBreakdown((v) => !v)}>
            {showRawBreakdown ? "Hide raw JSON" : "Show raw JSON"}
          </Button>
        }
      >
        <div className="pipeline-breakdown-grid">
          {Object.entries(breakdown as Record<string, any>)
            .filter(([proto, v]) => proto !== "unknown" || (v && Object.keys(v).length > 1))
            .flatMap(([proto, vendorsObj]) => {
              if (!vendorsObj || typeof vendorsObj !== "object") return [];
              return Object.entries(vendorsObj as Record<string, unknown>)
                .filter(([, count]) => typeof count === "number" && count > 0)
                .map(([vend, count]) => ({ proto, vend, count: count as number }));
            })
            .sort((a, b) => b.count - a.count)
            .map((x) => (
              <div key={`${x.proto}:${x.vend}`} className="pipeline-breakdown-card">
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <span className="pill">{PROTOCOL_DISPLAY[x.proto] ?? x.proto}</span>
                  <span className="muted" style={{ fontFamily: "var(--font-data)" }}>
                    →
                  </span>
                  <span className="pill">{VENDOR_DISPLAY[x.vend] ?? x.vend}</span>
                  <span className="muted" style={{ marginLeft: "auto", fontFamily: "var(--font-data)" }}>
                    {x.count} records
                  </span>
                </div>
              </div>
            ))}
        </div>

        {showRawBreakdown ? (
          <pre className="kvs" style={{ marginTop: 12 }}>
            <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(breakdown, null, 2)}</code>
          </pre>
        ) : null}
      </Panel>

      {filtered.map(([key, pv]) => (
        <Panel
          key={key}
          title={`${PROTOCOL_DISPLAY[pv.protocol] ?? pv.protocol} → ${VENDOR_DISPLAY[pv.vendor] ?? pv.vendor} → ISA-95 → ZeroBus`}
          subtitle={`${pv.recordCount} records observed`}
        >
          <div className="pipeline-flow">
            {pv.stages.map((s, idx) => {
              const stageNameKey = String(s.name);
              const display = STAGE_DISPLAY[stageNameKey] ?? s.name;
              const samples = Array.isArray(s.samples) ? s.samples : [];
              const samplesToShow = samples.slice(0, 3);

              return (
                <div key={`${key}-${idx}`} style={{ display: "contents" }}>
                  <div className="pipeline-stage">
                    <div className="pipeline-stage-header">
                      <div className="pipeline-stage-title">
                        {idx + 1}. {display}
                      </div>
                      <div className="pipeline-stage-count">{samples.length} samples</div>
                    </div>
                    {s.description ? <div className="pipeline-stage-desc">{s.description}</div> : <div className="pipeline-stage-desc muted"> </div>}

                    <div className="pipeline-stage-samples">
                      {samplesToShow.length === 0 ? (
                        <div className="muted" style={{ fontSize: 11 }}>
                          No samples yet
                        </div>
                      ) : (
                        samplesToShow.map((sample: any, sIdx: number) => {
                          const ts =
                            typeof sample?.timestamp === "number"
                              ? new Date(sample.timestamp * 1000).toLocaleTimeString()
                              : typeof sample?.timestamp === "string"
                                ? sample.timestamp
                                : "—";

                          // clean up noisy keys like legacy does
                          const jsonData: Record<string, unknown> = { ...(sample ?? {}) };
                          delete (jsonData as any).stage;
                          delete (jsonData as any).timestamp;
                          delete (jsonData as any).protocol;
                          delete (jsonData as any).protocol_type;

                          return (
                            <div key={`${key}-${idx}-${sIdx}`} className="pipeline-sample">
                              <div className="pipeline-sample-head">
                                <span style={{ fontWeight: 800, color: "var(--status-running)" }}>
                                  {VENDOR_DISPLAY[pv.vendor] ?? pv.vendor}
                                </span>
                                <span className="muted" style={{ fontFamily: "var(--font-data)" }}>
                                  {ts}
                                </span>
                              </div>
                              <pre className="kvs" style={{ margin: 0, maxHeight: 200 }}>
                                <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(jsonData, null, 2)}</code>
                              </pre>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>

                  {idx < pv.stages.length - 1 ? <div className="pipeline-arrow">→</div> : null}
                </div>
              );
            })}
          </div>
        </Panel>
      ))}
    </div>
  );
}

