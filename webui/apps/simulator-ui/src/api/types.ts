export type Protocol = "opcua" | "mqtt" | "modbus";

export type Health = { status?: string } | Record<string, unknown>;

export type IndustriesResponse = Array<{ name: string; sensor_count: number }>;

export type SensorsResponse = Record<
  string,
  {
    name: string;
    display_name?: string;
    sensor_count?: number;
    sensors?: unknown[];
    plc_name?: string;
    plc_vendor?: string;
    plc_model?: string;
  }
>;

export type ZeroBusConfigLoadResponse =
  | { success: true; config: any }
  | { success: false; message: string; detail?: string };

export type ZeroBusStatusResponse =
  | { success: true; status: Record<string, { active: boolean; has_config: boolean }> }
  | { success: false; message: string; detail?: string };

export type OpcuaNode = {
  name: string;
  type: "root" | "folder" | "plc" | "industry" | "sensor" | string;
  children?: OpcuaNode[];
  properties?: Record<string, string | number | boolean | null>;
  // Sensors
  path?: string;
  value?: number;
  unit?: string;
  quality?: string;
  forced?: boolean;
  min_value?: number;
  max_value?: number;
};

export type OpcuaHierarchyResponse = {
  root: string;
  children: OpcuaNode[];
};

export type ThingDescriptionResponse = Record<string, unknown>;

