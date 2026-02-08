import { Button, KvTable } from "@ot/ui-kit";
import { useMemo, useState } from "react";
import type { ThingDescriptionResponse } from "../api/types";
import { useAppToast } from "../toast/ToastContext";

type TabKey = "summary" | "properties" | "actions" | "events" | "raw";

function safeRecord(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
}

type WotProperty = {
  name: string;
  title: string;
  description: string;
  semanticType: string;
  unit: string;
  unitUri: string;
  industry: string;
  minimum?: number;
  maximum?: number;
  nodeId: string;
  browsePath: string;
};

function asString(v: unknown): string {
  return typeof v === "string" ? v : "";
}

function firstSemanticType(v: unknown): string {
  if (typeof v === "string") return v;
  if (Array.isArray(v) && typeof v[0] === "string") return v[0] as string;
  return "";
}

function isNum(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function badgeKindFromSemanticType(t: string): "saref" | "sosa" | "other" {
  if (t.startsWith("saref:")) return "saref";
  if (t.startsWith("sosa:")) return "sosa";
  return "other";
}

export function WotThingBrowser(props: { td: ThingDescriptionResponse | null }) {
  const toast = useAppToast();
  const [tab, setTab] = useState<TabKey>("properties");
  const [search, setSearch] = useState("");
  const [semanticType, setSemanticType] = useState("");
  const [industry, setIndustry] = useState("");
  const [unit, setUnit] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const tdObj = props.td ?? null;
  const propsRecord = useMemo(() => safeRecord(tdObj && (tdObj as any).properties), [tdObj]);
  const actionsRecord = useMemo(() => safeRecord(tdObj && (tdObj as any).actions), [tdObj]);
  const eventsRecord = useMemo(() => safeRecord(tdObj && (tdObj as any).events), [tdObj]);

  const properties = useMemo((): WotProperty[] => {
    const out: WotProperty[] = [];
    for (const [name, raw] of Object.entries(propsRecord)) {
      if (!raw || typeof raw !== "object" || Array.isArray(raw)) continue;
      const prop = raw as any;
      const forms0 = Array.isArray(prop.forms) && prop.forms[0] && typeof prop.forms[0] === "object" ? prop.forms[0] : {};

      out.push({
        name,
        title: asString(prop.title) || name,
        description: asString(prop.description),
        semanticType: firstSemanticType(prop["@type"]),
        unit: asString(prop.unit),
        unitUri: asString(prop["qudt:unit"]),
        industry: asString(prop["ex:industry"]),
        minimum: isNum(prop.minimum) ? prop.minimum : undefined,
        maximum: isNum(prop.maximum) ? prop.maximum : undefined,
        nodeId: asString(forms0["opcua:nodeId"]),
        browsePath: asString(forms0["opcua:browsePath"]),
      });
    }
    out.sort((a, b) => a.name.localeCompare(b.name));
    return out;
  }, [propsRecord]);

  const filterOptions = useMemo(() => {
    const sem = Array.from(new Set(properties.map((p) => p.semanticType).filter(Boolean))).sort((a, b) => a.localeCompare(b));
    const ind = Array.from(new Set(properties.map((p) => p.industry).filter(Boolean))).sort((a, b) => a.localeCompare(b));
    const units = Array.from(new Set(properties.map((p) => p.unit).filter(Boolean))).sort((a, b) => a.localeCompare(b));
    return { sem, ind, units };
  }, [properties]);

  const stats = useMemo(() => {
    const sem = new Set(properties.map((p) => p.semanticType).filter(Boolean));
    const ind = new Set(properties.map((p) => p.industry).filter(Boolean));
    const units = new Set(properties.map((p) => p.unit).filter(Boolean));
    return { total: properties.length, semanticTypes: sem.size, industries: ind.size, units: units.size };
  }, [properties]);

  const filteredProperties = useMemo(() => {
    const s = search.trim().toLowerCase();
    return properties.filter((p) => {
      const matchesSearch =
        !s ||
        p.name.toLowerCase().includes(s) ||
        p.title.toLowerCase().includes(s) ||
        (p.description || "").toLowerCase().includes(s);
      const matchesSemantic = !semanticType || p.semanticType === semanticType;
      const matchesIndustry = !industry || p.industry === industry;
      const matchesUnit = !unit || p.unit === unit;
      return matchesSearch && matchesSemantic && matchesIndustry && matchesUnit;
    });
  }, [properties, search, semanticType, industry, unit]);

  const summary = useMemo(() => {
    if (!tdObj) return null;
    // Keep this tight: show top-level identity + counts.
    const o = safeRecord(tdObj);
    const out: Record<string, unknown> = {};
    ["title", "id", "@type", "@context", "base", "description"].forEach((k) => {
      if (k in o) out[k] = o[k];
    });
    out["properties.count"] = properties.length;
    out["actions.count"] = Object.keys(actionsRecord).length;
    out["events.count"] = Object.keys(eventsRecord).length;
    out["semanticTypes.count"] = stats.semanticTypes;
    out["industries.count"] = stats.industries;
    out["units.count"] = stats.units;
    if ("security" in o) out["security"] = o["security"];
    if ("securityDefinitions" in o) out["securityDefinitions"] = o["securityDefinitions"];
    return out;
  }, [tdObj, properties.length, actionsRecord, eventsRecord, stats]);

  async function copyRaw() {
    try {
      if (!tdObj) return;
      await navigator.clipboard.writeText(JSON.stringify(tdObj, null, 2));
      toast.show("Copied Thing Description JSON", "ok");
    } catch {
      toast.show("Failed to copy to clipboard", "bad");
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        {(
          [
            ["summary", "Summary"],
            ["properties", `Properties (${properties.length})`],
            ["actions", `Actions (${Object.keys(actionsRecord).length})`],
            ["events", `Events (${Object.keys(eventsRecord).length})`],
            ["raw", "Raw JSON"],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            className={`btn ${tab === k ? "btn-primary" : "btn-secondary"}`}
            onClick={() => {
              setTab(k);
              setSearch("");
              setSemanticType("");
              setIndustry("");
              setUnit("");
              setExpanded(null);
            }}
          >
            {label}
          </button>
        ))}

        <div style={{ flex: 1 }} />

        <Button type="button" variant="secondary" onClick={copyRaw} disabled={!tdObj}>
          Copy JSON
        </Button>
      </div>

      {tab === "summary" ? (
        <KvTable data={summary} emptyText="No thing description loaded yet." />
      ) : tab === "raw" ? (
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(tdObj, null, 2)}</code>
        </pre>
      ) : tab !== "properties" ? (
        <KvTable data={tab === "actions" ? actionsRecord : eventsRecord} emptyText={`No ${tab} in thing description.`} maxRows={200} />
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          <div className="wot-stats-bar">
            <div className="wot-stat-card">
              <div className="wot-stat-label">Total Properties</div>
              <div className="wot-stat-value">{stats.total}</div>
            </div>
            <div className="wot-stat-card wot-lava">
              <div className="wot-stat-label">Semantic Types</div>
              <div className="wot-stat-value">{stats.semanticTypes}</div>
            </div>
            <div className="wot-stat-card wot-success">
              <div className="wot-stat-label">Industries</div>
              <div className="wot-stat-value">{stats.industries}</div>
            </div>
            <div className="wot-stat-card">
              <div className="wot-stat-label">W3C Compliant</div>
              <div className="wot-stat-value">✓</div>
            </div>
          </div>

          <div className="wot-controls">
            <div className="wot-search-row">
              <input
                className="input"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search properties by name…"
              />
            </div>
            <div className="wot-filter-row">
              <select className="input" value={semanticType} onChange={(e) => setSemanticType(e.target.value)}>
                <option value="">All Semantic Types</option>
                {filterOptions.sem.map((t) => (
                  <option value={t} key={t}>
                    {t}
                  </option>
                ))}
              </select>
              <select className="input" value={industry} onChange={(e) => setIndustry(e.target.value)}>
                <option value="">All Industries</option>
                {filterOptions.ind.map((t) => (
                  <option value={t} key={t}>
                    {t.replace(/_/g, " ").toUpperCase()}
                  </option>
                ))}
              </select>
              <select className="input" value={unit} onChange={(e) => setUnit(e.target.value)}>
                <option value="">All Units</option>
                {filterOptions.units.map((t) => (
                  <option value={t} key={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="wot-results-info">
            Showing <strong>{filteredProperties.length}</strong> of <strong>{properties.length}</strong> properties
          </div>

          {filteredProperties.length === 0 ? (
            <div className="muted" style={{ padding: 18 }}>
              No results. Try clearing filters.
            </div>
          ) : (
            <div className="wot-properties-grid">
              {filteredProperties.map((p) => {
                const semKind = badgeKindFromSemanticType(p.semanticType);
                const isExpanded = expanded === p.name;
                return (
                  <div
                    key={p.name}
                    className={`wot-property-card ${isExpanded ? "expanded" : ""}`}
                    role="button"
                    tabIndex={0}
                    onClick={() => setExpanded((cur) => (cur === p.name ? null : p.name))}
                  >
                    <div className="wot-property-header">
                      <div>
                        <div className="wot-property-name">{p.name}</div>
                        <div className="wot-property-title muted">{p.title}</div>
                      </div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
                        {p.semanticType ? (
                          <span className={`wot-badge ${semKind}`}>{p.semanticType}</span>
                        ) : (
                          <span className="wot-badge other">—</span>
                        )}
                        {p.industry ? <span className="wot-badge industry">{p.industry.replace(/_/g, " ")}</span> : null}
                        <span className="wot-badge opcua">opcua</span>
                      </div>
                    </div>

                    <div className="wot-property-details">
                      <div className="wot-detail">
                        <div className="wot-detail-label">Unit</div>
                        <div className="wot-detail-value">
                          {p.unit || "—"}{" "}
                          {p.unitUri ? (
                            <a className="wot-unit-uri" href={p.unitUri} target="_blank" rel="noreferrer">
                              (uri)
                            </a>
                          ) : null}
                        </div>
                      </div>
                      <div className="wot-detail">
                        <div className="wot-detail-label">Range</div>
                        <div className="wot-detail-value">
                          {isNum(p.minimum) || isNum(p.maximum) ? `${p.minimum ?? "—"} → ${p.maximum ?? "—"}` : "—"}
                        </div>
                      </div>
                      <div className="wot-detail">
                        <div className="wot-detail-label">NodeId</div>
                        <div className="wot-detail-value">{p.nodeId || "—"}</div>
                      </div>
                    </div>

                    {isExpanded ? (
                      <div className="wot-property-more">
                        {p.browsePath ? (
                          <div className="wot-more-row">
                            <div className="wot-detail-label">BrowsePath</div>
                            <div className="wot-detail-value">{p.browsePath}</div>
                          </div>
                        ) : null}
                        {p.description ? (
                          <div className="wot-more-row">
                            <div className="wot-detail-label">Description</div>
                            <div className="wot-detail-value">{p.description}</div>
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <div className="wot-hint muted">Click to expand</div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      <div className="muted">
        Tip: for the legacy full-page WoT browser, open <code>/wot/browser</code>.
      </div>
    </div>
  );
}

