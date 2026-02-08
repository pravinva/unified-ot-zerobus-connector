# React Web UI Parity Checklist (Connector + Simulator)

This document is the **source of truth** for “do not break existing functionality” while rebuilding the Web UIs in React.

## Connector UI (aiohttp) — current behavior to preserve

### Pages / routes
- **`GET /`**: UI landing page (will become React). Must remain reachable.
- **`GET /legacy`**: legacy vanilla UI (must remain reachable during migration).
- **`GET /static/*`**: static assets (CSS/JS/images). Must remain reachable.

### REST endpoints used by UI
- **Auth**
  - **`GET /api/auth/status`**: used to detect whether auth is enabled and whether user is logged in.
  - **`GET /api/auth/permissions`**: used to enable/disable UI actions based on permissions.
  - **`GET /api/auth/roles`**: role info (display / debugging).
  - **`GET /login`**, **`GET /login/callback`**, **`POST /logout`**: login/logout flow (React must keep cookie-based session behavior; all `fetch` must use `credentials: "include"`).
- **Overview badges**
  - Derived from **`GET /api/status`**: discovery count, configured/active sources, ZeroBus connection.
- **Discovery**
  - **`GET /api/discovery/servers?protocol=...`**: list discovered servers; protocol filter used.
  - **`POST /api/discovery/scan`**: trigger scan.
  - **`POST /api/discovery/test`**: test a server connection (expects `{ protocol, host, port }`).
- **Sources**
  - **`GET /api/sources`**: list configured sources.
  - **`POST /api/sources`**: create source.
  - **`PUT /api/sources/{name}`**: update source.
  - **`DELETE /api/sources/{name}`**: delete source.
  - **`POST /api/sources/{name}/start`**, **`POST /api/sources/{name}/stop`**: lifecycle control.
- **Bridge control**
  - **`POST /api/bridge/start`**, **`POST /api/bridge/stop`**
- **ZeroBus**
  - **`GET /api/zerobus/config`**: load current config; secrets may be masked.
  - **`POST /api/zerobus/config`**: save config; **must preserve secret-handling semantics** (blank secret should not wipe stored secret).
  - **`POST /api/zerobus/start`**, **`POST /api/zerobus/stop`**
  - **`GET /api/zerobus/diagnostics?deep=true|false`**: diagnostics; rendered as terminal-ish output.
- **Monitoring**
  - **`GET /api/status`**: rendered as key/value list (values must appear green).
  - **`GET /api/metrics`**: rendered as key/value list (values must appear green).
  - **`GET /api/diagnostics/pipeline`**: pipeline visualization + samples.
- **Health**
  - **`GET /health`**

### Visual/UX invariants
- **SCADA control room theme**: reuse the existing theme tokens (notably `--status-running: #00ff41`) and dense panel layout.
- **Diagnostics/log aesthetics**:
  - Key/value values render in **green** (currently `.kv .v { color: var(--text-accent); }` where `--text-accent` is green).
  - Terminal-ish blocks use dark background + monospace + scroll.

## Simulator UI (aiohttp + WebSocket) — current behavior to preserve

### Pages / routes
- **`GET /`**: UI landing page (will become React).
- **`GET /legacy`**: legacy template UI (must remain reachable during migration).
- **`GET /wot/browser`**: WoT browser page.
- **`GET /api/health`**: health check.
- **`GET /ws`**: WebSocket endpoint for real-time updates and NLP commands.

### REST endpoints (non-exhaustive but required for parity)
- **Sensors & industries**
  - **`GET /api/sensors`**
  - **`GET /api/industries`**
- **OPC-UA / WoT**
  - **`GET /api/opcua/hierarchy`**
  - **`GET /api/opcua/thing-description`**
- **Raw stream**
  - **`GET /api/raw-data-stream`**
- **ZeroBus (per protocol)**
  - **`POST /api/zerobus/config/load`**
  - **`POST /api/zerobus/config`**
  - **`POST /api/zerobus/test`**
  - **`POST /api/zerobus/start`**
  - **`POST /api/zerobus/stop`**
  - **`GET /api/zerobus/status`**
- **Protocol monitoring**
  - **`GET /api/protocols/opcua/clients`**
  - **`GET /api/protocols/mqtt/subscribers`**
- **Vendor modes**
  - **`GET /api/modes`**
  - **`GET /api/modes/{mode_type}`**
  - **`POST /api/modes/{mode_type}/toggle`**
  - **`POST /api/modes/{mode_type}/protocol/toggle`**
  - **`GET /api/modes/{mode_type}/diagnostics`**
  - **`GET /api/modes/messages/recent`**
  - **`GET /api/modes/topics/active`**
  - **`GET /api/modes/metrics/comprehensive`**
  - **`GET /api/connection/endpoints`**

### WebSocket message types (client → server)
- **`{ type: "subscribe", sensors: string[] }`**: subscribe to sensor updates.
- **`{ type: "unsubscribe", sensors: string[] }`**: unsubscribe.
- **`{ type: "nlp_command", text: string, history?: unknown[] }`**: natural-language command path.
- **`{ type: "get_status" }`**: request current status.
- **`{ type: "set_update_rate", interval: number }`**: set update interval (clamped server-side).

### WebSocket message types (server → client) (minimum)
- **`{ type: "subscribed", sensors: string[] }`**
- **`{ type: "unsubscribed", sensors: string[] }`**
- **`{ type: "update_rate_changed", interval: number }`**
- **`{ type: "error", message: string }`**
- **`{ type: "nlp_response", ... }`** (shape depends on command; must be displayed in UI)

