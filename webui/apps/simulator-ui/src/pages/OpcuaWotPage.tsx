import { Button, Panel } from "@ot/ui-kit";
import { useCallback, useEffect, useState } from "react";
import { simApi } from "../api/simApi";
import type { OpcuaHierarchyResponse, ThingDescriptionResponse } from "../api/types";
import { OpcuaTree } from "../components/OpcuaTree";
import { WotThingBrowser } from "../components/WotThingBrowser";
import { useAppToast } from "../toast/ToastContext";

export function OpcuaWotPage() {
  const toast = useAppToast();
  const [hier, setHier] = useState<OpcuaHierarchyResponse | null>(null);
  const [td, setTd] = useState<ThingDescriptionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [h, t] = await Promise.all([simApi.getOpcuaHierarchy(), simApi.getThingDescription()]);
      setHier(h);
      setTd(t);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load OPC-UA/WoT data", "bad");
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
        title="OPC-UA / WoT"
        subtitle="Hierarchy browser + Thing Description"
        actions={
          <div style={{ display: "flex", gap: 10 }}>
            <Button type="button" onClick={() => refresh()} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
            <a href="/wot/browser" style={{ textDecoration: "none" }}>
              <Button type="button">Open WoT browser</Button>
            </a>
          </div>
        }
      >
        <div className="muted">
          Uses <code>/api/opcua/hierarchy</code> and <code>/api/opcua/thing-description</code>.
        </div>
      </Panel>

      <Panel title="OPC-UA hierarchy" subtitle="Browsable node tree (live values)">
        <OpcuaTree data={hier} refresh={refresh} refreshMs={500} />
      </Panel>

      <Panel title="Thing Description" subtitle="WoT browser (properties/actions/events)">
        <WotThingBrowser td={td} />
      </Panel>
    </div>
  );
}

