import type { ReactNode } from "react";

export type PillKind = "ok" | "warn" | "bad";

export function StatusPill(props: { kind: PillKind; children: ReactNode }) {
  return <span className={`pill ${props.kind}`.trim()}>{props.children}</span>;
}

