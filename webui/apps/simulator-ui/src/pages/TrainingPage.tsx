import { Button, Field, Panel, TextInput } from "@ot/ui-kit";
import { useCallback, useEffect, useState } from "react";
import { simApi } from "../api/simApi";
import { useAppToast } from "../toast/ToastContext";

export function TrainingPage() {
  const toast = useAppToast();
  const [sensorPath, setSensorPath] = useState("");
  const [value, setValue] = useState("");
  const [duration, setDuration] = useState("60");
  const [traineeId, setTraineeId] = useState("operator1");

  const [scenarios, setScenarios] = useState<any>(null);
  const [leaderboard, setLeaderboard] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [s, l] = await Promise.all([simApi.listScenarios(), simApi.leaderboard()]);
      setScenarios(s);
      setLeaderboard(l);
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Failed to load training data", "bad");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    refresh().catch(() => {});
  }, [refresh]);

  const inject = useCallback(async () => {
    const dur = Number(duration);
    const val: any = value;
    try {
      const res = await simApi.injectData(sensorPath.trim(), val, Number.isFinite(dur) ? dur : undefined);
      setResult(JSON.stringify(res, null, 2));
      toast.show("Injection sent", "ok");
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Inject failed", "bad");
    }
  }, [duration, sensorPath, toast, value]);

  const runScenario = useCallback(
    async (scenario_id: string) => {
      try {
        const res = await simApi.runScenario(scenario_id, traineeId.trim());
        setResult(JSON.stringify(res, null, 2));
        toast.show("Scenario started", "ok");
      } catch (e) {
        toast.show(e instanceof Error ? e.message : "Run scenario failed", "bad");
      }
    },
    [toast, traineeId]
  );

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <Panel
        title="Training"
        subtitle="Fault injection, scenarios, replay"
        actions={
          <Button type="button" onClick={() => refresh()} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <div className="muted" style={{ marginBottom: 10 }}>
          Uses <code>/api/training/*</code> endpoints (inject, scenarios, run, submit diagnosis, leaderboard).
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 10 }}>
          <Field label="Sensor path">
            <TextInput value={sensorPath} onChange={(e) => setSensorPath(e.target.value)} placeholder="mining.crusher.bearing_temp" />
          </Field>
          <Field label="Value">
            <TextInput value={value} onChange={(e) => setValue(e.target.value)} placeholder="95.5" />
          </Field>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginTop: 10 }}>
          <Field label="Duration (seconds)">
            <TextInput value={duration} onChange={(e) => setDuration(e.target.value)} placeholder="60" />
          </Field>
          <Field label="Trainee ID">
            <TextInput value={traineeId} onChange={(e) => setTraineeId(e.target.value)} placeholder="operator1" />
          </Field>
          <div style={{ display: "flex", alignItems: "end" }}>
            <Button variant="primary" type="button" onClick={() => inject()}>
              Inject
            </Button>
          </div>
        </div>
      </Panel>

      <Panel title="Scenarios" subtitle="Run a saved fault scenario">
        <div style={{ display: "grid", gap: 10 }}>
          {Array.isArray((scenarios as any)?.scenarios)
            ? (scenarios as any).scenarios.map((s: any) => (
                <div key={String(s?.scenario_id ?? s?.name ?? "")} style={{ border: "1px solid var(--border-panel)", borderRadius: 2, padding: 12 }}>
                  <div className="section-title">{String(s?.name ?? s?.scenario_id ?? "Scenario")}</div>
                  <div className="muted" style={{ marginTop: 6 }}>
                    {String(s?.description ?? "")}
                  </div>
                  <div style={{ marginTop: 10 }}>
                    <Button variant="primary" type="button" onClick={() => runScenario(String(s?.scenario_id))}>
                      Run
                    </Button>
                  </div>
                </div>
              ))
            : (
                <div className="muted">No scenarios loaded yet.</div>
              )}
        </div>
      </Panel>

      <Panel title="Leaderboard" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{JSON.stringify(leaderboard, null, 2)}</code>
        </pre>
      </Panel>

      <Panel title="Last result" subtitle="Raw JSON">
        <pre className="kvs" style={{ margin: 0 }}>
          <code style={{ color: "var(--text-primary)" }}>{result || "—"}</code>
        </pre>
      </Panel>
    </div>
  );
}

