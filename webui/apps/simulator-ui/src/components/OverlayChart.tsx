import { useMemo } from "react";

const PALETTE = [
  "#00ff41", // green
  "#00a8e1", // cyan
  "#ffaa00", // amber
  "#4a9eff", // blue
  "#ff3621", // lava
  "#c77dff", // purple
  "#2dd4bf", // teal
  "#f472b6", // pink
];

function clamp(n: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, n));
}

function fmt(n: number | null | undefined): string {
  if (typeof n !== "number" || !Number.isFinite(n)) return "—";
  const abs = Math.abs(n);
  if (abs >= 1000) return n.toFixed(0);
  if (abs >= 10) return n.toFixed(1);
  return n.toFixed(2);
}

export function OverlayChart(props: {
  series: Array<{ key: string; label: string; color?: string; values: number[] }>;
  height?: number;
  maxPoints?: number;
}) {
  const height = props.height ?? 260;
  const maxPoints = props.maxPoints ?? 240;

  const normalized = useMemo(() => {
    const s = props.series.map((x, idx) => ({
      ...x,
      color: x.color ?? PALETTE[idx % PALETTE.length],
      values: x.values.slice(-maxPoints),
    }));

    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    for (const line of s) {
      for (const v of line.values) {
        if (!Number.isFinite(v)) continue;
        min = Math.min(min, v);
        max = Math.max(max, v);
      }
    }
    if (!Number.isFinite(min) || !Number.isFinite(max)) {
      min = 0;
      max = 1;
    }
    if (min === max) {
      min -= 1;
      max += 1;
    }

    return { series: s, min, max };
  }, [maxPoints, props.series]);

  const width = 1000; // viewBox width; scales to container
  const padX = 24;
  const padY = 18;
  const plotW = width - padX * 2;
  const plotH = height - padY * 2;

  const yFor = (v: number) => {
    const t = (v - normalized.min) / (normalized.max - normalized.min);
    const yy = padY + (1 - clamp(t, 0, 1)) * plotH;
    return yy;
  };

  const xForIndex = (i: number, n: number) => {
    if (n <= 1) return padX;
    return padX + (i / (n - 1)) * plotW;
  };

  const gridLines = 6;

  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div
        style={{
          border: "1px solid var(--border-panel)",
          borderRadius: 2,
          background: "rgba(0,0,0,0.35)",
          overflow: "hidden",
        }}
      >
        <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="none">
          {/* grid */}
          {Array.from({ length: gridLines + 1 }).map((_, idx) => {
            const y = padY + (idx / gridLines) * plotH;
            const v = normalized.max - (idx / gridLines) * (normalized.max - normalized.min);
            return (
              <g key={idx}>
                <line x1={padX} x2={padX + plotW} y1={y} y2={y} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
                <text x={6} y={y + 4} fill="rgba(255,255,255,0.45)" fontSize="18" fontFamily="var(--font-data)">
                  {fmt(v)}
                </text>
              </g>
            );
          })}

          {/* lines */}
          {normalized.series.map((line) => {
            const n = line.values.length;
            if (n < 2) return null;
            const d = line.values
              .map((v, i) => `${i === 0 ? "M" : "L"} ${xForIndex(i, n)} ${yFor(v)}`)
              .join(" ");
            return (
              <path
                key={line.key}
                d={d}
                fill="none"
                stroke={line.color}
                strokeWidth="2"
                strokeLinejoin="round"
                strokeLinecap="round"
                opacity="0.9"
              />
            );
          })}
        </svg>
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {normalized.series.map((s) => {
          const last = s.values.length ? s.values[s.values.length - 1] : undefined;
          return (
            <div
              key={s.key}
              className="pill ok"
              style={{
                borderColor: s.color,
                color: s.color,
                background: "rgba(0,0,0,0.25)",
              }}
              title={s.label}
            >
              <span style={{ fontFamily: "var(--font-data)", fontWeight: 900 }}>{s.label}</span>
              <span style={{ fontFamily: "var(--font-data)", opacity: 0.85 }}>{fmt(last)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

