import { Button, Field, Panel, TextInput } from "@ot/ui-kit";
import { useMemo, useState } from "react";
import { useSimulatorWs } from "../ws/useSimulatorWs";
import { useAppToast } from "../toast/ToastContext";

export function NlpPage() {
  const toast = useAppToast();
  const ws = useSimulatorWs();
  const [text, setText] = useState("");
  const [subList, setSubList] = useState("");

  const logLines = useMemo(() => {
    return ws.nlpLog
      .slice(-100)
      .map((l) => `${new Date(l.ts).toLocaleTimeString()} ${l.direction === "out" ? ">>" : "<<"} ${JSON.stringify(l.payload)}`)
      .join("\n");
  }, [ws.nlpLog]);

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel title="NLP / WebSocket" subtitle="Live status + start/stop + chat commands">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <span className="muted">Connection:</span>
          <span style={{ fontFamily: "var(--font-data)" }}>{ws.connected ? "connected" : "disconnected"}</span>
          <Button type="button" onClick={() => ws.getStatus()} disabled={!ws.connected}>
            Get status
          </Button>
        </div>
      </Panel>

      <Panel title="Chat / commands" subtitle={'Sends { type: "nlp_command" } over /ws'}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 140px", gap: 10 }}>
          <TextInput
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder='Examples: "start opcua", "stop mqtt", "status"'
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                const ok = ws.sendNlpCommand(text.trim());
                if (!ok) toast.show("WebSocket not connected", "warn");
                setText("");
              }
            }}
          />
          <Button
            variant="primary"
            type="button"
            onClick={() => {
              const ok = ws.sendNlpCommand(text.trim());
              if (!ok) toast.show("WebSocket not connected", "warn");
              setText("");
            }}
            disabled={!ws.connected}
          >
            Send
          </Button>
        </div>

        <pre className="kvs" style={{ marginTop: 10, marginBottom: 0, maxHeight: 360 }}>
          <code style={{ color: "var(--text-primary)" }}>{logLines || "No messages yet."}</code>
        </pre>
      </Panel>

      <Panel title="Sensor subscriptions" subtitle="Subscribe/unsubscribe to sensor paths">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 140px 140px", gap: 10, alignItems: "end" }}>
          <Field label="Sensors (comma-separated)">
            <TextInput value={subList} onChange={(e) => setSubList(e.target.value)} placeholder="mining.crusher.bearing_temp, ..." />
          </Field>
          <Button
            type="button"
            onClick={() => {
              const sensors = subList.split(",").map((s) => s.trim()).filter(Boolean);
              const ok = ws.subscribe(sensors);
              if (!ok) toast.show("WebSocket not connected", "warn");
            }}
            disabled={!ws.connected}
          >
            Subscribe
          </Button>
          <Button
            variant="danger"
            type="button"
            onClick={() => {
              const sensors = subList.split(",").map((s) => s.trim()).filter(Boolean);
              const ok = ws.unsubscribe(sensors);
              if (!ok) toast.show("WebSocket not connected", "warn");
            }}
            disabled={!ws.connected}
          >
            Unsubscribe
          </Button>
        </div>
        <div className="muted" style={{ marginTop: 10 }}>
          Latest sensor_data payload (raw):
        </div>
        <pre className="kvs" style={{ marginTop: 8, marginBottom: 0, maxHeight: 280 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(ws.sensorData, null, 2)}</code>
        </pre>
      </Panel>
    </div>
  );
}

