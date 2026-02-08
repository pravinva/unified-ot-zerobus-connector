import { Button, KvTable, Panel } from "@ot/ui-kit";
import { useCallback, useEffect, useState } from "react";
import { connectorApi } from "../api/connectorApi";
import type { ConnectorStatus } from "../api/types";
import { useAuthState } from "../auth/AuthContext";
import { useAppToast } from "../toast/ToastContext";

export function StatusPage() {
  const toast = useAppToast();
  const { can } = useAuthState();
  const [data, setData] = useState<ConnectorStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!can.read) return;
    setLoading(true);
    try {
      setData(await connectorApi.getStatus());
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load status", "bad");
    } finally {
      setLoading(false);
    }
  }, [can.read, toast]);

  useEffect(() => {
    refresh().catch(() => {});
    const t = window.setInterval(() => refresh().catch(() => {}), 5000);
    return () => window.clearInterval(t);
  }, [refresh]);

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="Status"
        subtitle="Live connector state (values are green by design)"
        actions={
          <Button type="button" onClick={() => refresh()} disabled={loading || !can.read}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <KvTable data={data} />
        <div className="muted" style={{ marginTop: 10 }}>
          Driven by <code>/api/status</code>.
        </div>
      </Panel>
    </div>
  );
}

