export type WsClientMessage =
  | { type: "subscribe"; sensors: string[] }
  | { type: "unsubscribe"; sensors: string[] }
  | { type: "nlp_command"; text: string; history?: unknown[] }
  | { type: "get_status" }
  | { type: "set_update_rate"; interval: number };

export type WsServerMessage =
  | { type: "status_update"; timestamp: number; simulators: Record<string, unknown>; vendor_modes?: Record<string, unknown> }
  | { type: "sensor_data"; timestamp: number; sensors: Record<string, unknown> }
  | { type: "subscribed"; sensors: string[] }
  | { type: "unsubscribed"; sensors: string[] }
  | { type: "update_rate_changed"; interval: number }
  | { type: "nlp_response"; [k: string]: unknown }
  | { type: "error"; message: string }
  | Record<string, unknown>;

