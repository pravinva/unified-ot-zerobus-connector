# Deployment Status - OT Simulator & IoT Connector

**Date:** 2026-01-19
**Status:** ✅ Both Containers Running Successfully

---

## Running Containers

### 1. OT Simulator with Training Platform

**Container Details:**
- **Name:** `ot-simulator-training`
- **Container ID:** `21e2d951b729`
- **Image:** `ot-simulator:latest`
- **Status:** Up 13 minutes
- **User:** Non-root (otsim)

**Port Mappings:**
| Host Port | Container Port | Protocol | Purpose |
|-----------|----------------|----------|---------|
| 8989 | 8989 | HTTP | Web UI + Training Platform + REST APIs |
| 4840 | 4840 | OPC-UA | OPC-UA Server endpoint |
| 1883 | 1883 | MQTT | MQTT Broker |
| 5020 | 5020 | Modbus TCP | Modbus TCP Server |

**Access Points:**
- **Web UI with Training Platform:** http://localhost:8989
- **OPC-UA Server:** `opc.tcp://localhost:4840/ot-simulator/server/`
- **MQTT Broker:** `localhost:1883`
- **Modbus TCP Server:** `localhost:5020`

**Training Platform Features:**
- ✅ Inject Faults (single + batch)
- ✅ Training Scenarios (create, save, run)
- ✅ CSV Upload & Replay
- ✅ Leaderboard & Performance Tracking
- ✅ 10 REST API endpoints functional
- ✅ Natural language interface (Claude Sonnet 4.5)

**Key Services:**
- 80 sensors across 4 industries (mining, utilities, manufacturing, oil & gas)
- Multi-protocol simulator (OPC-UA, MQTT, Modbus)
- Real-time sensor monitoring
- Operations AI Assistant

---

### 2. IoT Connector

**Container Details:**
- **Name:** `iot-connector`
- **Container ID:** `a21d243810b1`
- **Image:** `iot-connector:latest`
- **Status:** Up 1 minute
- **User:** Non-root (iotconnector)

**Port Mappings:**
| Host Port | Container Port | Protocol | Purpose |
|-----------|----------------|----------|---------|
| 8080 | 8080 | HTTP | Web GUI + REST APIs |
| 9090 | 9090 | HTTP | Prometheus Metrics |

**Access Points:**
- **Web GUI:** http://localhost:8080
- **Prometheus Metrics:** http://localhost:9090/metrics

**Configuration:**
- Target table: `test.test.test`
- Active sources: 0 (configure via web UI)
- ZeroBus: Disabled (configure via web UI)
- Backpressure: Queue size 10000, spool enabled
- Spool directory: `/app/spool`
- DLQ directory: `/app/spool/dlq`

**Key Features:**
- Multi-protocol support (OPC-UA, MQTT, Modbus)
- Protocol auto-detection from endpoint URLs
- Unified data ingestion to Databricks ZeroBus
- Circuit breaker for fault tolerance
- Backpressure handling with spillover to disk
- Prometheus metrics for monitoring

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OT Simulator (8989)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  OPC-UA      │  │    MQTT      │  │   Modbus     │     │
│  │  :4840       │  │   :1883      │  │   :5020      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                  ┌─────────▼─────────┐                      │
│                  │  Training Platform│                      │
│                  │  (Web UI + APIs)  │                      │
│                  └───────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Protocol connections
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    IoT Connector (8080)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          UnifiedBridge (Protocol Clients)            │  │
│  │    ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │    │ OPC-UA   │  │  MQTT    │  │ Modbus   │        │  │
│  │    │ Client   │  │ Client   │  │ Client   │        │  │
│  │    └────┬─────┘  └────┬─────┘  └────┬─────┘        │  │
│  │         └─────────────┬─────────────┘               │  │
│  │                       │                              │  │
│  │         ┌─────────────▼──────────────┐              │  │
│  │         │  Backpressure Manager      │              │  │
│  │         │  (Queue + Spool + DLQ)     │              │  │
│  │         └─────────────┬──────────────┘              │  │
│  │                       │                              │  │
│  │         ┌─────────────▼──────────────┐              │  │
│  │         │     ZeroBus Client         │              │  │
│  │         │  (Databricks Ingestion)    │              │  │
│  │         └────────────────────────────┘              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Databricks Workspace                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Unity Catalog Delta Tables               │  │
│  │    (main.iot.sensor_telemetry)                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start Guide

### Access Training Platform

1. Open web browser: http://localhost:8989
2. Click **"🎯 Training Platform"** card to expand
3. Explore 4 tabs:
   - **Inject Faults**: Single or batch fault injection
   - **Scenarios**: Create and run multi-step training scenarios
   - **CSV Upload**: Upload historical data for replay
   - **Leaderboard**: View trainee performance metrics

### Configure IoT Connector

1. Open web browser: http://localhost:8080
2. Click **"Add Source"** to configure OT protocol connections
3. Example OPC-UA source:
   ```
   Endpoint: opc.tcp://localhost:4840/ot-simulator/server/
   Protocol: Auto-detected (OPC-UA)
   ```
4. Click **"Configure ZeroBus"** to set up Databricks connection
5. Start data ingestion

### Test Training API

```bash
# List all sensors
curl http://localhost:8989/api/sensors?industry=mining

# Inject fault into bearing temperature sensor
curl -X POST http://localhost:8989/api/training/inject_data \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_path": "mining/crusher_1_bearing_temp",
    "value": 95.5,
    "duration_seconds": 60,
    "fault_type": "fixed_value"
  }'

# List all training scenarios
curl http://localhost:8989/api/training/scenarios

# Get leaderboard
curl http://localhost:8989/api/training/leaderboard
```

### Test IoT Connector API

```bash
# Health check
curl http://localhost:8080/api/health

# Get connector status
curl http://localhost:8080/api/status

# List configured sources
curl http://localhost:8080/api/sources

# Prometheus metrics
curl http://localhost:9090/metrics
```

---

## Container Management

### View Logs

```bash
# Simulator logs
docker logs -f ot-simulator-training

# Connector logs
docker logs -f iot-connector

# Filter for specific keywords
docker logs ot-simulator-training | grep -i "training"
docker logs iot-connector | grep -i "error"
```

### Stop Containers

```bash
# Stop simulator
docker stop ot-simulator-training

# Stop connector
docker stop iot-connector

# Stop both
docker stop ot-simulator-training iot-connector
```

### Restart Containers

```bash
# Restart simulator
docker restart ot-simulator-training

# Restart connector
docker restart iot-connector
```

### Remove Containers

```bash
# Remove simulator (must be stopped first)
docker stop ot-simulator-training && docker rm ot-simulator-training

# Remove connector (must be stopped first)
docker stop iot-connector && docker rm iot-connector
```

### Rebuild and Run

```bash
# Simulator
cd /Users/pravin.varma/Documents/Demo/opc-ua-zerobus-connector
docker build -t ot-simulator:latest -f Dockerfile.simulator .
docker run -d --name ot-simulator-training \
  -p 8989:8989 -p 4840:4840 -p 1883:1883 -p 5020:5020 \
  ot-simulator:latest

# Connector
docker build -t iot-connector:latest -f Dockerfile.connector .
docker run -d --name iot-connector \
  -p 8080:8080 -p 9090:9090 \
  iot-connector:latest
```

---

## Deployment Files

### Scripts

1. **`/tmp/build_and_run_simulator.sh`**
   - Automated script to build and run simulator container
   - Includes health checks and status reporting

2. **`/tmp/run_simulator_container.sh`**
   - Quick script to run simulator container (assumes image exists)

### Dockerfiles

1. **`Dockerfile.simulator`**
   - Location: `/Users/pravin.varma/Documents/Demo/opc-ua-zerobus-connector/Dockerfile.simulator`
   - Base image: `python:3.11-slim`
   - User: `otsim` (non-root)
   - Exposes: 4840 (OPC-UA), 1883 (MQTT), 5020 (Modbus), 8989 (Web UI)

2. **`Dockerfile.connector`**
   - Location: `/Users/pravin.varma/Documents/Demo/opc-ua-zerobus-connector/Dockerfile.connector`
   - Base image: `python:3.11-slim`
   - User: `iotconnector` (non-root)
   - Exposes: 8080 (Web GUI), 9090 (Prometheus)

### Documentation

1. **`DOCKER_DEPLOYMENT_GUIDE.md`** - Comprehensive Docker deployment guide
2. **`TRAINING_UI_USER_GUIDE.md`** - Training Platform user guide
3. **`GUI_TRAINING_INTEGRATION_STATUS.md`** - Integration status and features
4. **`TRAINING_API_NAVIGATION.md`** - Complete API reference

---

## Troubleshooting

### Issue: Container Won't Start

```bash
# Check logs for errors
docker logs ot-simulator-training
docker logs iot-connector

# Common causes:
# 1. Port conflicts - check if ports are already in use
lsof -i :8989  # or :8080, :4840, etc.

# 2. Missing dependencies - rebuild image
docker build --no-cache -t ot-simulator:latest -f Dockerfile.simulator .
```

### Issue: Can't Connect to Web UI

```bash
# Verify container is running
docker ps | grep ot-simulator

# Check port mappings
docker port ot-simulator-training

# Test connectivity
curl http://localhost:8989/api/health
curl http://localhost:8080/api/health
```

### Issue: Training Platform Not Visible

- **Symptom:** Can't see "🎯 Training Platform" card in web UI
- **Solution:** Training Platform is a **collapsible card** - click the card header to expand
- **Verification:** Check HTML source: `curl -s http://localhost:8989 | grep "Training Platform"`

### Issue: Connector Shows 0 Sources

- **Symptom:** Connector logs show "Active sources: 0"
- **Solution:** This is normal - sources must be configured via web UI
- **Action:** Open http://localhost:8080 and click "Add Source"

---

## Next Steps

### Option 1: Configure Connector to Ingest Simulator Data

1. Open connector web UI: http://localhost:8080
2. Add OPC-UA source:
   - Endpoint: `opc.tcp://ot-simulator-training:4840/ot-simulator/server/`
   - Note: Use container name `ot-simulator-training` instead of `localhost` for inter-container communication
3. Configure ZeroBus connection to Databricks workspace
4. Start data ingestion

### Option 2: Test Training Platform Features

1. Open simulator web UI: http://localhost:8989
2. Click "🎯 Training Platform" to expand
3. Try injecting a fault:
   - Sensor: `mining/crusher_1_bearing_temp`
   - Value: `95.5`
   - Duration: `60` seconds
4. Watch sensor values change in real-time

### Option 3: Deploy to Databricks Apps

See `DATABRICKS_APPS_DEPLOYMENT.md` for complete guide:

```bash
# Tag images for Databricks workspace registry
docker tag ot-simulator:latest <workspace-url>.azurecr.io/ot-simulator:latest
docker tag iot-connector:latest <workspace-url>.azurecr.io/iot-connector:latest

# Push to registry
docker push <workspace-url>.azurecr.io/ot-simulator:latest
docker push <workspace-url>.azurecr.io/iot-connector:latest

# Deploy via Databricks CLI
databricks apps deploy ot-simulator-app --image <workspace-url>.azurecr.io/ot-simulator:latest
databricks apps deploy iot-connector-app --image <workspace-url>.azurecr.io/iot-connector:latest
```

---

## Production Readiness

### ✅ Completed

- ✅ Both containers running successfully
- ✅ Non-root users configured for security
- ✅ Multi-protocol support (OPC-UA, MQTT, Modbus)
- ✅ Training Platform fully integrated (10 REST API endpoints)
- ✅ Natural language interface operational
- ✅ Web UIs accessible (ports 8989, 8080)
- ✅ Prometheus metrics exposed (port 9090)
- ✅ Comprehensive documentation

### 🔄 Next Phase

- Configure connector sources via web UI
- Set up ZeroBus connection to Databricks
- Test end-to-end data flow (simulator → connector → Unity Catalog)
- Deploy to Databricks Apps for remote access
- Set up monitoring dashboards (Grafana + Prometheus)
- Create training scenarios library
- Conduct pilot testing with 20 trainees

---

## Support

For questions or issues:

1. **Check Logs:** `docker logs -f <container-name>`
2. **Review Documentation:** See `DOCKER_DEPLOYMENT_GUIDE.md`
3. **API Reference:** See `TRAINING_API_NAVIGATION.md`
4. **Troubleshooting:** See troubleshooting sections in all docs

---

**Deployment completed successfully on 2026-01-19**
