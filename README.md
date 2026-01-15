## Databricks IoT Connector (Edge)

A **professional-grade edge connector** supporting **OPC-UA, MQTT, and Modbus** protocols, streaming data to Databricks via Zerobus. Runs as **ONE Docker container** in the DMZ/edge (Purdue Model Level 3.5), bridging OT and IT networks securely.

### Key Features

- **Multi-Protocol Support**: OPC-UA, MQTT (TLS), Modbus TCP/RTU
- **Natural Language Control**: AI-powered operator using Claude Sonnet 4.5
- **Automatic Reconnection**: Exponential backoff after network outages
- **Backpressure Handling**: Configurable queue limits and drop policies
- **Rate Limiting**: Prevent overwhelming downstream systems
- **Local Web UI**: Professional interface on **port 8080**
- **Prometheus Metrics**: Comprehensive monitoring on **port 9090**
- **Zero Dependencies**: Runs anywhere Docker runs

### Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python -m opcua2uc --config ./config.yaml
```

Open:
- Web UI: `http://localhost:8080`
- Metrics: `http://localhost:9090/metrics`

### Docker run

```bash
docker build -t opcua2uc:dev .
docker run --rm -p 8080:8080 -p 9090:9090 opcua2uc:dev
```

## Supported Protocols

### OPC-UA (OPC Unified Architecture)
- Industrial automation standard
- Subscription-based data change notifications
- Automatic variable discovery
- **Endpoint**: `opc.tcp://hostname:port`

### MQTT (Message Queuing Telemetry Transport)
- Lightweight pub/sub protocol
- Support for TLS/SSL (mqtts://)
- Wildcard topic subscriptions
- JSON, string, and binary payload parsing
- **Endpoint**: `mqtt://hostname:port` or `mqtts://hostname:port`

### Modbus (TCP & RTU)
- Master-slave protocol
- Holding/input registers, coils, discrete inputs
- Serial (RTU) and Ethernet (TCP) support
- Configurable scaling and offsets
- **Endpoint**: `modbus://hostname:port` or `modbusrtu:///dev/ttyUSB0`

**Configuration**: Protocol settings are configured in `ot_simulator/config.yaml`. See the inline comments for OPC UA security modes, MQTT TLS settings, and Modbus register mappings.

### Quick Start Examples

```yaml
sources:
  # OPC-UA
  - name: "plc-1"
    endpoint: "opc.tcp://192.168.1.100:4840"
    protocol_type: "opcua"
    variable_limit: 25
    publishing_interval_ms: 1000

  # MQTT
  - name: "sensors"
    endpoint: "mqtt://192.168.1.200:1883"
    protocol_type: "mqtt"
    topics: ["sensors/+/temperature"]
    qos: 1

  # Modbus TCP
  - name: "meter-1"
    endpoint: "modbus://192.168.1.50:502"
    protocol_type: "modbus"
    unit_id: 1
    registers:
      - type: "holding"
        address: 0
        count: 10
        name: "power"
        scale: 0.1
```

More examples in [`examples/`](examples/) directory.

### REST API (served by the connector)

- `GET /api/status` - Connector status and metrics
- `GET /api/sources` - List configured sources
- `POST /api/sources` - Add new source (auto-detects protocol)
- `DELETE /api/sources/{name}` - Remove source
- `POST /api/sources/{name}/test` - Test connection (all protocols)
- `POST /api/sources/{name}/start` - Start streaming
- `POST /api/sources/{name}/stop` - Stop streaming
- `GET /api/config` - Get full configuration
- `POST /api/config` - Update configuration
- `POST /api/config/patch` - Partial config update
- `POST /api/protocol/detect` - Detect protocol from endpoint
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

### Natural Language Operator

Control the simulator using plain English powered by **Claude Sonnet 4.5**:

```bash
# Start the LLM agent
python -m ot_simulator.llm_agent_operator

🎤 You: "start the simulator for mining opcua"
🤖 Agent: ✓ OPCUA started
💭 Starting OPC-UA protocol server on port 4840...

🎤 You: "inject a fault into the crusher for 30 seconds"
🤖 Agent: ✓ Fault injected into mining/crusher_1_motor_power
💭 Simulating crusher motor failure for testing...
```

**Features:**
- Natural language understanding (not regex patterns)
- Conversational memory (remembers context)
- 380+ sensors across 16 industries (mining, utilities, renewable energy, manufacturing, oil & gas, and more)
- 6 command types: start, stop, inject_fault, status, list_sensors, chat

**Quick Start:**
```bash
# Terminal 1: Start simulator
python -m ot_simulator --protocol all --web-ui

# Terminal 2: Start LLM agent
python -m ot_simulator.llm_agent_operator
```

**Documentation:**
- `QUICK_START_NATURAL_LANGUAGE.md` - 5-minute quick start
- `NATURAL_LANGUAGE_OPERATOR_GUIDE.md` - Comprehensive guide (400+ lines)
- `NATURAL_LANGUAGE_SUMMARY.md` - Complete technical summary
- `ot_simulator/llm_agent_config.yaml` - Configuration file

**Configuration:**
Edit `ot_simulator/llm_agent_config.yaml` to customize model endpoint, API URL, and LLM parameters.

---

### Databricks auth

This connector expects a Databricks **service principal** (you mentioned: `sp-opcua`) using OAuth client credentials.

Set env vars on the edge host:
- `DBX_CLIENT_ID`
- `DBX_CLIENT_SECRET`

Then call `POST /api/databricks/test_auth` to validate.


### Destination table (Unity Catalog)

All protocols stream to a unified table with this schema:

```sql
CREATE TABLE IF NOT EXISTS iot.sensors.raw_events (
  event_time TIMESTAMP,              -- Event timestamp (microseconds)
  ingest_time TIMESTAMP,             -- Ingestion timestamp
  source_name STRING,                -- Source identifier
  endpoint STRING,                   -- Connection endpoint
  protocol_type STRING,              -- opcua, mqtt, or modbus
  topic_or_path STRING,              -- Protocol-specific path
  value STRING,                      -- Value as string
  value_type STRING,                 -- Data type
  value_num DOUBLE,                  -- Numeric value (if applicable)
  metadata MAP<STRING, STRING>,      -- Protocol-specific metadata
  status_code INT,                   -- Quality/status code
  status STRING                      -- Status description
);
```

Example configured target: `manufacturing.iot_data.events_bronze`

### Architecture

#### Purdue Model Compliant Deployment

The connector respects industrial security architecture (ISA-95/IEC-62443 Purdue Model):

```
┌──────────────────────────────────────────────────────────────────┐
│ Level 5: Enterprise Network (IT)                                │
│                                                                  │
│              ┌──────────────────────┐                            │
│              │   Databricks Cloud   │                            │
│              │   Unity Catalog      │                            │
│              │   Delta Tables       │                            │
│              └──────────▲───────────┘                            │
└─────────────────────────┼────────────────────────────────────────┘
                          │ HTTPS/gRPC (TLS)
┌─────────────────────────┼────────────────────────────────────────┐
│ Level 3.5: DMZ / Edge (Industrial Firewall)                     │
│                          │                                       │
│              ┌───────────▼───────────┐                           │
│              │  IoT Edge Connector   │  ← This Project          │
│              │  (Docker Container)   │                           │
│              │  ┌─────────────────┐  │                           │
│              │  │ OPC UA Client   │  │                           │
│              │  │ MQTT Client     │  │                           │
│              │  │ Modbus Client   │  │                           │
│              │  └─────────────────┘  │                           │
│              │  ┌─────────────────┐  │                           │
│              │  │ Zerobus gRPC    │  │                           │
│              │  │ Buffering/Queue │  │                           │
│              │  └─────────────────┘  │                           │
│              └───────────▲───────────┘                           │
└─────────────────────────┼────────────────────────────────────────┘
                          │ One-way diode (data flows UP only)
┌─────────────────────────┼────────────────────────────────────────┐
│ Level 2: Control Network (OT - Isolated from IT)                │
│                          │                                       │
│    ┌─────────────┐  ┌───▼──────┐  ┌─────────────┐              │
│    │  OPC UA     │  │  MQTT    │  │  Modbus     │              │
│    │  Servers    │  │  Broker  │  │  Devices    │              │
│    │  (PLCs)     │  │ (Sensors)│  │  (RTUs)     │              │
│    └─────────────┘  └──────────┘  └─────────────┘              │
│                                                                  │
│ Level 1: Supervisory Control (SCADA/HMI)                        │
│ Level 0: Field Devices (Physical Processes)                     │
└──────────────────────────────────────────────────────────────────┘
```

**Security Principles**:
- Connector deploys in **DMZ** (Level 3.5), NOT inside plant network (Level 0-2)
- **One-way data flow**: OT → DMZ → Cloud (no commands flow down)
- **Firewall isolation**: OT network remains isolated from IT/Internet
- **Read-only OPC UA/MQTT/Modbus subscriptions** (no writes to PLC)
- **TLS/mTLS**: All cloud communication encrypted
- **No inbound connections**: Connector initiates all connections

### Simulator Architecture: How Everything Works

The OT simulator has a **3-layer architecture** that separates data generation, data access, and data exposure:

#### Layer 1: Data Generation (Always Running)
- **SensorSimulator** instances generate realistic industrial sensor data
- 380+ sensors across 16 industries (mining, utilities, renewable energy, manufacturing, etc.)
- Sensors start immediately at startup and run continuously
- **Independent of protocols** - sensors don't "belong to" any specific protocol

#### Layer 2: Data Access (Always Available)
- **SimulatorManager** provides unified access to all sensors
- `get_sensor_value(path)` returns current reading from any sensor
- **Fault injection happens here** - modifies sensor values at the source
- Used by both protocols and WebSocket server

#### Layer 3: Data Exposure (Optional - Controlled by Start/Stop)
- **OPC-UA Simulator**: Network endpoint at `opc.tcp://0.0.0.0:4840`
- **MQTT Simulator**: Publishes to MQTT broker
- **Modbus Simulator**: TCP/RTU endpoint
- **WebSocket Server**: Real-time streaming to browser charts

#### Key Architectural Insights

**Charts vs Protocols:**
- **Charts** get data directly from SimulatorManager via WebSocket (Layer 2)
- **Charts work WITHOUT starting any protocols** - they bypass Layer 3 entirely
- Charts subscribe to specific sensors and receive updates every 500ms

**Protocol Start/Stop:**
- Starting a protocol only creates the **network endpoint** (Layer 3)
- Stopping a protocol only closes the **network endpoint**
- **Underlying sensors keep running regardless** (Layer 1 always active)

**Fault Injection:**
- Faults are injected at the **SensorSimulator level** (Layer 1)
- Faulty data propagates to **ALL consumers** simultaneously:
  - OPC-UA clients see the fault
  - MQTT subscribers see the fault
  - Modbus masters see the fault
  - Web UI charts see the fault
- Everyone sees the same faulty reading because they all read from the same source

**Data Flow Example:**
```
User clicks "Add Chart" for mining/crusher_1_motor_power
    ↓
JavaScript sends WebSocket message: {type: "subscribe", sensors: [...]}
    ↓
WebSocketServer.handle_message() adds to subscriptions
    ↓
broadcast_sensor_data() loop (every 500ms)
    ↓
SimulatorManager.get_sensor_value("mining/crusher_1_motor_power")
    ↓
Returns current value from SensorSimulator instance
    ↓
WebSocket sends JSON to browser: {type: "sensor_data", sensors: {...}}
    ↓
Chart.js renders the point
```

**Protocol Independence:**
```
OPC-UA client connects → reads from Layer 3 (OPC-UA endpoint)
                              ↓
                         Layer 2 (SimulatorManager)
                              ↓
                         Layer 1 (Same SensorSimulator instance)
                              ↑
                         Layer 2 (SimulatorManager)
                              ↑
Chart subscribes via WebSocket → reads from Layer 2 directly
```

Both get data from the same source, through completely different paths.

### Features Detail

#### Backpressure Handling
- Configurable in-memory queue per source
- Drop policies: `drop_oldest` (keep recent) or `drop_newest` (preserve history)
- Prometheus metrics for queue depth and drops

#### Automatic Reconnection
- Exponential backoff with configurable delays
- Per-source reconnection settings
- Survives network outages gracefully

#### Rate Limiting
- Token bucket algorithm
- Per-second record limits
- Prevents overwhelming Databricks/Zerobus

### Monitoring

Prometheus metrics available at `http://localhost:9090/metrics`:

```
connector_connected_sources                    # Active connections
connector_events_ingested_total                # Events received from sources
connector_events_sent_total                    # Events sent to Databricks
connector_events_dropped_total{source="..."}   # Dropped due to backpressure
connector_queue_depth{source="..."}            # Current queue size
```

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (when available)
pytest

# Format code
black opcua2uc/

# Type check
mypy opcua2uc/
```

### Production Deployment

1. **Build container**:
   ```bash
   docker build -t my-registry/iot-connector:v1.0 .
   docker push my-registry/iot-connector:v1.0
   ```

2. **Set environment variables**:
   ```bash
   export DBX_CLIENT_ID="your-service-principal-client-id"
   export DBX_CLIENT_SECRET="your-service-principal-secret"
   ```

3. **Deploy**:
   ```bash
   docker run -d \
     --name iot-connector \
     --restart unless-stopped \
     -p 8080:8080 -p 9090:9090 \
     -e DBX_CLIENT_ID -e DBX_CLIENT_SECRET \
     -v /path/to/config.yaml:/app/config.yaml \
     my-registry/iot-connector:v1.0 \
     --config /app/config.yaml
   ```

4. **Monitor**:
   - Web UI: `http://<host>:8080`
   - Metrics: `http://<host>:9090/metrics`
   - Logs: `docker logs -f iot-connector`

### Troubleshooting

**Common Issues**:
- Connection fails: Check firewall, endpoint, and credentials
- Events dropped: Increase queue size or rate limits
- High memory: Reduce queue size or variable/register counts
- Protocol-specific issues: See inline comments in `ot_simulator/config.yaml`
- Reconnection loops: Check network stability and reconnection settings

### Contributing

This is an internal project. For issues or feature requests, contact the Databricks field engineering team.

### License

Proprietary - Databricks Inc.

