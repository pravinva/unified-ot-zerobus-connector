import { Button, Panel } from "@ot/ui-kit";
import { useCallback, useEffect, useState } from "react";
import { simApi } from "../api/simApi";
import { useAppToast } from "../toast/ToastContext";

export function ConnectionsPage() {
  const toast = useAppToast();
  const [endpoints, setEndpoints] = useState<any>(null);
  const [opcuaClients, setOpcuaClients] = useState<any>(null);
  const [mqttSubs, setMqttSubs] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [e, o, m] = await Promise.all([simApi.getConnectionEndpoints(), simApi.getOpcuaClients(), simApi.getMqttSubscribers()]);
      setEndpoints(e);
      setOpcuaClients(o);
      setMqttSubs(m);
    } catch (err) {
      toast.show(err instanceof Error ? err.message : "Failed to load connections", "bad");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    refresh().catch(() => {});
  }, [refresh]);

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="Connections"
        subtitle="Clients, subscribers, and endpoints"
        actions={
          <Button type="button" onClick={() => refresh()} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <div className="muted">
          Uses <code>/api/connection/endpoints</code>, <code>/api/protocols/opcua/clients</code>, and{" "}
          <code>/api/protocols/mqtt/subscribers</code>.
        </div>
      </Panel>

      <Panel title="Connection endpoints" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(endpoints, null, 2)}</code>
        </pre>
      </Panel>

      <Panel title="OPC-UA clients" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(opcuaClients, null, 2)}</code>
        </pre>
      </Panel>

      <Panel title="MQTT subscribers" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(mqttSubs, null, 2)}</code>
        </pre>
      </Panel>
    </div>
  );
}

