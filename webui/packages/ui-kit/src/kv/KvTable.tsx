import { useMemo, useState } from "react";

function stableEntries(obj: unknown): Array<[string, unknown]> {
  if (!obj || typeof obj !== "object") return [];
  return Object.entries(obj as Record<string, unknown>);
}

export function KvTable(props: { data: unknown; emptyText?: string; className?: string; maxRows?: number }) {
  const entries = useMemo(() => stableEntries(props.data), [props.data]);
  const maxRows = props.maxRows ?? 200;
  const [showAll, setShowAll] = useState(false);
  if (entries.length === 0) {
    return <div className={`muted ${props.className ?? ""}`.trim()}>{props.emptyText ?? "No data"}</div>;
  }

  const visible = showAll ? entries : entries.slice(0, maxRows);

  return (
    <div className={`kvs ${props.className ?? ""}`.trim()}>
      {visible.map(([k, v]) => (
        <div className="kv" key={k}>
          <div className="k">{k}</div>
          <div className="v">{typeof v === "string" ? v : JSON.stringify(v, null, 2)}</div>
        </div>
      ))}
      {entries.length > maxRows && (
        <div style={{ paddingTop: 10 }}>
          <button className="btn btn-secondary" type="button" onClick={() => setShowAll((v) => !v)}>
            {showAll ? `Show first ${maxRows}` : `Show all (${entries.length})`}
          </button>
        </div>
      )}
    </div>
  );
}

