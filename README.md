# Unified OT/IoT → Databricks ZeroBus Connector

This repo contains:
- **`unified_connector/`**: a multi-protocol edge connector (OPC-UA, MQTT, Modbus) with a lightweight Web UI, and streaming to Databricks via **ZeroBus**.
- **`ot_simulator/`**: an OT data simulator you can use to generate sample OPC-UA/MQTT/Modbus data.

---

## What it does (current behavior)

- **Discovery**: scans configured subnets and lists reachable **OPC-UA servers**, **MQTT brokers**, and **Modbus TCP servers**.
- **Sources**: you configure sources (protocol + endpoint) and start/stop them individually.
- **Bridge**: starts “infrastructure” (ZeroBus client + batching) without auto-starting all sources.
- **ZeroBus streaming**: batches records and writes to your Unity Catalog table via ZeroBus ingest.
- **Diagnostics-first UI**: discovery “Test” shows detailed output in-panel.

---

## Purdue / ISA‑95 deployment model (recommended)

The connector is typically deployed in **Level 3.5 (DMZ)** so OT stays isolated and data flows **up** only:

```
┌──────────────────────────────────────────────┐
│ Level 5/4: Enterprise / IT                   │
│                                              │
│   Databricks Workspace (UC + Delta tables)   │
└──────────────────────────▲───────────────────┘
                           │ HTTPS/gRPC (TLS)
┌──────────────────────────┼───────────────────┐
│ Level 3.5: DMZ / Edge Gateway                │
│                                              │
│   Unified Connector (this repo)              │
│   - OPC-UA client / MQTT client / Modbus     │
│   - buffering + batching                     │
│   - ZeroBus ingest client                    │
└──────────────────────────▲───────────────────┘
                           │ OT protocols (read-only)
┌──────────────────────────┼───────────────────┐
│ Level 2/1/0: OT Network                       │
│                                              │
│   PLCs / OPC-UA Servers / MQTT Brokers /     │
│   Modbus Devices                              │
└──────────────────────────────────────────────┘
```

---

## Run locally (repo)

### Start the connector

```bash
cd "/Users/pravin.varma/Documents/Demo/unified-ot-zerobus-connector"
.venv312/bin/python -m unified_connector --log-level INFO
```

Open Web UI: `http://127.0.0.1:8080`

### Start bridge + start all configured sources

```bash
curl -sS -X POST http://127.0.0.1:8080/api/bridge/start -H 'Content-Type: application/json' -d '{}' >/dev/null && \
curl -sS http://127.0.0.1:8080/api/sources | .venv312/bin/python -c 'import sys,json,urllib.parse; d=json.load(sys.stdin); print("\n".join(["curl -sS -X POST http://127.0.0.1:8080/api/sources/%s/start -H \"Content-Type: application/json\" -d \"{}\" >/dev/null" % urllib.parse.quote(s[\"name\"], safe=\"\") for s in (d.get(\"sources\") or [])]))' | bash
```

### Stop the local app (kills anything listening on 8080)

```bash
lsof -tiTCP:8080 -sTCP:LISTEN | xargs -r kill -9
```

---

## Run in Docker (Colima)

This repo includes a Colima-friendly compose file:
- **`docker-compose.unified-connector.colima.yml`**

### Start

```bash
cd "/Users/pravin.varma/Documents/Demo/unified-ot-zerobus-connector"
colima start
docker compose -f docker-compose.unified-connector.colima.yml up -d --build
```

Web UI: `http://127.0.0.1:8080`

### Stop

```bash
cd "/Users/pravin.varma/Documents/Demo/unified-ot-zerobus-connector"
docker compose -f docker-compose.unified-connector.colima.yml down
```

### Start bridge + start all sources (Docker)

Same API command (because ports are published to the host):

```bash
curl -sS -X POST http://127.0.0.1:8080/api/bridge/start -H 'Content-Type: application/json' -d '{}' >/dev/null && \
curl -sS http://127.0.0.1:8080/api/sources | python3 -c 'import sys,json,urllib.parse; d=json.load(sys.stdin); print("\n".join(["curl -sS -X POST http://127.0.0.1:8080/api/sources/%s/start -H \"Content-Type: application/json\" -d \"{}\" >/dev/null" % urllib.parse.quote(s[\"name\"], safe=\"\") for s in (d.get(\"sources\") or [])]))' | bash
```

---

## How the code flows (high level)

```
Web UI (HTML/JS)
  └─> aiohttp routes (unified_connector/web/web_server.py)
        ├─ /api/discovery/*  -> DiscoveryService (unified_connector/core/discovery.py)
        ├─ /api/sources/*    -> config + per-source start/stop (UnifiedBridge)
        ├─ /api/bridge/start -> start_infra() (ZeroBus + batching only)
        └─ /api/metrics      -> bridge/backpressure/zerobus counters

Protocol clients (OPC-UA / MQTT / Modbus)
  └─> UnifiedBridge queue (backpressure)
        └─> ZeroBus client batches -> Unity Catalog table
```

---

## Configuration

- Main config: `unified_connector/config/config.yaml`
- Normalization config: `unified_connector/config/normalization_config.yaml`

**Security note**: do not commit ZeroBus secrets. Configure credentials via the UI, env vars, or local credential store.

### Proxy Configuration (Purdue Layer 3.5)

For deployments in Layer 3.5 (DMZ) that need to route cloud traffic through a corporate proxy:

**Option 1: Web UI**
1. Navigate to the ZeroBus configuration section
2. Enable "Proxy Settings (for Purdue Layer 3.5)"
3. Configure:
   - **Enable Proxy**: Check to enable proxy support
   - **Use Environment Variables**: Check to use HTTP_PROXY/HTTPS_PROXY env vars
   - **HTTP Proxy**: e.g., `http://proxy.company.com:8080`
   - **HTTPS Proxy**: e.g., `http://proxy.company.com:8080`
   - **No Proxy**: Comma-separated hosts to bypass (e.g., `localhost,127.0.0.1,.internal`)

**Option 2: config.yaml**
```yaml
zerobus:
  enabled: true
  proxy:
    enabled: true
    use_env_vars: true  # Use HTTP_PROXY/HTTPS_PROXY from environment
    http_proxy: "http://proxy.company.com:8080"
    https_proxy: "http://proxy.company.com:8080"
    no_proxy: "localhost,127.0.0.1"
```

**Option 3: Environment Variables**
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

**Option 4: Docker Compose**
```yaml
services:
  unified-connector:
    environment:
      - HTTP_PROXY=http://proxy.company.com:8080
      - HTTPS_PROXY=http://proxy.company.com:8080
      - NO_PROXY=localhost,127.0.0.1
```

**Network Flow with Proxy:**
```
OT Devices (Layer 2/3) - REMOTE, NOT localhost
  └─> Unified Connector (Layer 3.5)
        ├─> Local OT Network (NO PROXY - Direct Connection)
        │   - OPC-UA Server 1: opc.tcp://192.168.20.100:4840
        │   - OPC-UA Server 2: opc.tcp://10.5.10.50:4841
        │   - MQTT Broker: mqtt://192.168.20.200:1883
        │   - Modbus Device: modbus://172.16.5.100:502
        │
        └─> Databricks Cloud (THROUGH PROXY on 443)
            - Workspace API: https://workspace.cloud.databricks.com
            - ZeroBus: *.zerobus.*.cloud.databricks.com
```

**IMPORTANT**: OT devices are typically **NOT on localhost** - they are remote devices on your plant/factory network (192.168.x.x, 10.x.x.x, 172.16.x.x). The `no_proxy` setting uses CIDR notation to bypass the proxy for entire network ranges.

