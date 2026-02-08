import { apiJson } from "./client";
import type {
  Health,
  IndustriesResponse,
  OpcuaHierarchyResponse,
  Protocol,
  SensorsResponse,
  ThingDescriptionResponse,
  ZeroBusConfigLoadResponse,
  ZeroBusStatusResponse,
} from "./types";

export const simApi = {
  getHealth: () => apiJson<Health>("/api/health"),
  getIndustries: () => apiJson<IndustriesResponse>("/api/industries"),
  getSensors: () => apiJson<SensorsResponse>("/api/sensors"),

  // ZeroBus
  loadZeroBusConfig: (protocol: Protocol) =>
    apiJson<ZeroBusConfigLoadResponse>("/api/zerobus/config/load", { method: "POST", body: JSON.stringify({ protocol }) }),
  saveZeroBusConfig: (protocol: Protocol, config: any) =>
    apiJson<any>("/api/zerobus/config", { method: "POST", body: JSON.stringify({ protocol, config }) }),
  testZeroBus: (protocol: Protocol, config: any) =>
    apiJson<any>("/api/zerobus/test", { method: "POST", body: JSON.stringify({ protocol, config }) }),
  startZeroBus: (protocol: Protocol) => apiJson<any>("/api/zerobus/start", { method: "POST", body: JSON.stringify({ protocol }) }),
  stopZeroBus: (protocol: Protocol) => apiJson<any>("/api/zerobus/stop", { method: "POST", body: JSON.stringify({ protocol }) }),
  zeroBusStatus: () => apiJson<ZeroBusStatusResponse>("/api/zerobus/status"),

  // Protocol clients/subscribers
  getOpcuaClients: () => apiJson<any>("/api/protocols/opcua/clients"),
  getMqttSubscribers: () => apiJson<any>("/api/protocols/mqtt/subscribers"),
  getConnectionEndpoints: () => apiJson<any>("/api/connection/endpoints"),

  // Vendor modes
  getModes: () => apiJson<any>("/api/modes"),
  getMode: (modeType: string) => apiJson<any>(`/api/modes/${encodeURIComponent(modeType)}`),
  toggleMode: (modeType: string) => apiJson<any>(`/api/modes/${encodeURIComponent(modeType)}/toggle`, { method: "POST", body: "{}" }),
  toggleModeProtocol: (modeType: string, protocol: Protocol) =>
    apiJson<any>(`/api/modes/${encodeURIComponent(modeType)}/protocol/toggle`, {
      method: "POST",
      body: JSON.stringify({ protocol }),
    }),
  modeDiagnostics: (modeType: string) => apiJson<any>(`/api/modes/${encodeURIComponent(modeType)}/diagnostics`),
  recentMessages: () => apiJson<any>("/api/modes/messages/recent"),
  activeTopics: () => apiJson<any>("/api/modes/topics/active"),
  comprehensiveMetrics: () => apiJson<any>("/api/modes/metrics/comprehensive"),

  // OPC-UA / WoT
  getOpcuaHierarchy: () => apiJson<OpcuaHierarchyResponse>("/api/opcua/hierarchy"),
  getThingDescription: () => apiJson<ThingDescriptionResponse>("/api/opcua/thing-description"),

  // Training
  injectData: (sensor_path: string, value: unknown, duration_seconds?: number) =>
    apiJson<any>("/api/training/inject_data", { method: "POST", body: JSON.stringify({ sensor_path, value, duration_seconds }) }),
  listScenarios: () => apiJson<any>("/api/training/scenarios"),
  runScenario: (scenario_id: string, trainee_id: string) =>
    apiJson<any>("/api/training/run_scenario", { method: "POST", body: JSON.stringify({ scenario_id, trainee_id }) }),
  leaderboard: () => apiJson<any>("/api/training/leaderboard"),
};

