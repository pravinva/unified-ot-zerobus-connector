import { useEffect, useMemo, useRef, useState } from "react";
import type { OpcuaHierarchyResponse, OpcuaNode } from "../api/types";

const SEARCH_ALIASES: Record<string, string> = {
  temperature: "temp",
  pressure: "press",
  vibration: "vib",
  position: "pos",
  current: "curr",
  voltage: "volt",
  frequency: "freq",
  humidity: "hum",
  conveyor: "conv",
};

function expandSearchTerm(term: string): string[] {
  const lower = term.toLowerCase();
  for (const [fullWord, abbrev] of Object.entries(SEARCH_ALIASES)) {
    if (lower.includes(fullWord)) {
      return [term, term.replace(new RegExp(fullWord, "gi"), abbrev)];
    }
  }
  return [term];
}

function makeNodeKey(parentKey: string, node: Pick<OpcuaNode, "type" | "path" | "name">): string {
  // For sensors, `path` is globally unique and stable across refreshes.
  if (node.type === "sensor" && node.path) return `sensor:${node.path}`;
  return parentKey ? `${parentKey}/${node.name}` : node.name;
}

function walk(node: OpcuaNode, parentKey: string, fn: (n: OpcuaNode, key: string) => void) {
  const key = makeNodeKey(parentKey, node);
  fn(node, key);
  node.children?.forEach((c) => walk(c, key, fn));
}

function filterTree(
  root: { name: string; type: "root"; children: OpcuaNode[] },
  searchTerm: string
): { filtered: { name: string; type: "root"; children: OpcuaNode[] }; expandKeys: Set<string> } {
  const terms = expandSearchTerm(searchTerm).map((t) => t.toLowerCase()).filter(Boolean);
  const expandKeys = new Set<string>();

  const matchesNode = (n: OpcuaNode) => {
    const hay = `${n.name ?? ""} ${n.type ?? ""} ${n.path ?? ""}`.toLowerCase();
    return terms.some((t) => hay.includes(t));
  };

  const filterNode = (n: OpcuaNode, parent: string): OpcuaNode | null => {
    const key = makeNodeKey(parent, n);
    const childMatches = (n.children || [])
      .map((c) => filterNode(c, key))
      .filter((x): x is OpcuaNode => x !== null);

    const selfMatch = matchesNode(n);
    const hasMatch = selfMatch || childMatches.length > 0;
    if (!hasMatch) return null;

    // If children matched, auto-expand parents during search.
    if (childMatches.length > 0) expandKeys.add(key);

    return {
      ...n,
      children: childMatches.length > 0 ? childMatches : n.children,
    };
  };

  const children = root.children
    .map((c) => filterNode(c, root.name))
    .filter((x): x is OpcuaNode => x !== null);

  return { filtered: { ...root, children }, expandKeys };
}

export function OpcuaTree(props: {
  data: OpcuaHierarchyResponse | null;
  refresh: () => Promise<void>;
  refreshMs?: number;
}) {
  const { data, refresh, refreshMs = 500 } = props;
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(["Objects"]));
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [updatedPaths, setUpdatedPaths] = useState<Set<string>>(() => new Set());

  const inFlight = useRef(false);
  const prevValues = useRef<Map<string, number>>(new Map());
  const clearTimers = useRef<Map<string, number>>(new Map());

  const root = useMemo(() => {
    if (!data) return null;
    return { name: data.root || "Objects", type: "root" as const, children: data.children || [] };
  }, [data]);

  const { viewRoot, searchExpand } = useMemo(() => {
    if (!root) return { viewRoot: null as typeof root, searchExpand: new Set<string>() };
    if (!search.trim()) return { viewRoot: root, searchExpand: new Set<string>() };
    const r = filterTree(root, search.trim());
    return { viewRoot: r.filtered, searchExpand: r.expandKeys };
  }, [root, search]);

  // Poll for value updates while enabled.
  useEffect(() => {
    if (!autoRefresh) return;
    const id = window.setInterval(async () => {
      if (inFlight.current) return;
      inFlight.current = true;
      try {
        await refresh();
      } finally {
        inFlight.current = false;
      }
    }, refreshMs);
    return () => window.clearInterval(id);
  }, [autoRefresh, refresh, refreshMs]);

  // Track sensor value changes to flash updated values.
  useEffect(() => {
    if (!root) return;
    const changed = new Set<string>();

    root.children.forEach((c) => {
      walk(c, root.name, (n) => {
        if (n.type !== "sensor" || !n.path || typeof n.value !== "number") return;
        const prev = prevValues.current.get(n.path);
        if (prev !== undefined && prev !== n.value) changed.add(n.path);
        prevValues.current.set(n.path, n.value);
      });
    });

    if (changed.size === 0) return;

    setUpdatedPaths((prev) => {
      const next = new Set(prev);
      changed.forEach((p) => next.add(p));
      return next;
    });

    // Clear after 500ms per path.
    changed.forEach((p) => {
      const existing = clearTimers.current.get(p);
      if (existing) window.clearTimeout(existing);
      const t = window.setTimeout(() => {
        setUpdatedPaths((prev) => {
          const next = new Set(prev);
          next.delete(p);
          return next;
        });
        clearTimers.current.delete(p);
      }, 500);
      clearTimers.current.set(p, t);
    });
  }, [root]);

  const isExpanded = (k: string) => {
    if (search.trim()) return searchExpand.has(k) || expanded.has(k);
    return expanded.has(k);
  };

  const toggle = (k: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  };

  const renderNode = (n: OpcuaNode, parent: string) => {
    const k = makeNodeKey(parent, n);
    const hasChildren = (n.children?.length || 0) > 0;
    const hasProps = !!(n.properties && Object.keys(n.properties).length > 0);
    const canExpand = hasChildren || hasProps;
    const expandedNow = canExpand && isExpanded(k);

    const icon =
      n.type === "root" || n.type === "folder"
        ? "▸"
        : n.type === "plc"
          ? "⊙"
          : n.type === "industry"
            ? "◆"
            : n.type === "sensor"
              ? "●"
              : "○";

    const onHeaderClick = () => {
      if (!canExpand) return;
      toggle(k);
    };

    const qualityClass = n.forced
      ? "forced"
      : (n.quality || "").toLowerCase().includes("uncertain")
        ? "uncertain"
        : (n.quality || "").toLowerCase().includes("bad")
          ? "bad"
          : "good";

    return (
      <div className="tree-node" key={k}>
        <div
          className={`tree-node-header${expandedNow ? " active" : ""}`}
          onClick={onHeaderClick}
          data-sensor-path={n.type === "sensor" ? n.path : undefined}
          role="button"
          tabIndex={0}
        >
          <span className={`tree-chevron${expandedNow ? " expanded" : ""}${canExpand ? "" : " leaf"}`}>▶</span>
          <span className="tree-icon">{icon}</span>
          <span className="tree-label">{n.name}</span>

          {n.type === "sensor" ? (
            <>
              <span className={`tree-value${n.path && updatedPaths.has(n.path) ? " updated" : ""}`}>
                {typeof n.value === "number" ? n.value.toFixed(2) : "--"}
              </span>
              <span className="tree-unit">{n.unit || ""}</span>
              <span className={`tree-quality ${qualityClass}`}>{n.forced ? "forced" : n.quality || "good"}</span>
            </>
          ) : null}
        </div>

        {canExpand ? (
          <div className={`tree-children${expandedNow ? " expanded" : ""}`}>
            {hasProps ? (
              <div className="tree-properties">
                {Object.entries(n.properties || {}).map(([key, value]) => (
                  <div className="tree-property" key={`${k}:${key}`}>
                    <span className="tree-property-name">{key}:</span>
                    <span className="tree-property-value">{String(value)}</span>
                  </div>
                ))}
              </div>
            ) : null}
            {hasChildren ? n.children!.map((c) => renderNode(c, k)) : null}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <input
          className="opcua-search-input"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder='Search nodes… (e.g. "crusher", "temperature", "freq")'
        />
        <label className="muted" style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
          Auto-refresh
        </label>
      </div>

      <div className="opcua-tree-container">
        {!viewRoot ? (
          <div className="muted">No hierarchy loaded yet.</div>
        ) : (
          <div>{renderNode({ name: viewRoot.name, type: "root", children: viewRoot.children }, "")}</div>
        )}
      </div>
    </div>
  );
}

