# Docker Deployment Guide - OT Simulator with Training Platform

## Overview

This guide explains how to deploy the OT Simulator with integrated Training Platform using Docker containers.

---

## Quick Start

### Option 1: Automated Script (Recommended)

Run the automated deployment script from your terminal:

```bash
bash /tmp/build_and_run_simulator.sh
```

This script will:
1. Build the `ot-simulator:latest` Docker image
2. Stop and remove any existing container
3. Start a new container with all ports exposed
4. Show container status and logs
5. Display access points

### Option 2: Manual Docker Commands

```bash
# Navigate to project directory
cd /Users/pravin.varma/Documents/Demo/opc-ua-zerobus-connector

# Build the image
docker build --no-cache -t ot-simulator:latest -f Dockerfile.simulator .

# Stop and remove old container (if exists)
docker stop ot-simulator-1 2>/dev/null || true
docker rm ot-simulator-1 2>/dev/null || true

# Run the container
docker run -d \
  --name ot-simulator-1 \
  -p 8989:8989 \
  -p 4840:4840 \
  -p 1883:1883 \
  -p 5020:5020 \
  ot-simulator:latest

# View logs
docker logs -f ot-simulator-1
```

### Option 3: Docker Compose

```bash
# Use pre-configured docker-compose file
docker-compose -f docker-compose.simulator1.yml up -d

# View logs
docker-compose -f docker-compose.simulator1.yml logs -f
```

---

## Port Mappings

| Host Port | Container Port | Protocol | Description |
|-----------|----------------|----------|-------------|
| 8989 | 8989 | HTTP | Web UI + Training Platform + REST APIs |
| 4840 | 4840 | OPC-UA | OPC-UA Server endpoint |
| 1883 | 1883 | MQTT | MQTT Broker |
| 5020 | 5020 | Modbus TCP | Modbus TCP Server |

---

## Access Points

### Web UI with Training Platform
**URL:** http://localhost:8989

**Features:**
- Protocol Control Panel (start/stop OPC-UA, MQTT, Modbus simulators)
- Real-time Sensor Monitoring
- **🎯 Training Platform** (click to expand):
  - Tab 1: Inject Faults (single or batch)
  - Tab 2: Scenarios (create, save, run multi-step training scenarios)
  - Tab 3: CSV Upload (drag-drop historical data for replay)
  - Tab 4: Leaderboard (trainee performance metrics)
- Operations AI Assistant (natural language interface powered by Claude Sonnet 4.5)

### Industrial Protocol Endpoints

**OPC-UA Server:**
```
opc.tcp://localhost:4840/ot-simulator/server/
```

**MQTT Broker:**
```
Host: localhost
Port: 1883
Topics: mining/+, utilities/+, manufacturing/+, oil_gas/+
```

**Modbus TCP Server:**
```
Host: localhost
Port: 5020
Unit ID: 1
Registers: 0-79 (80 sensors)
```

---

## REST API Endpoints

### Health Check
```bash
curl http://localhost:8989/api/health
```

### Training Platform APIs

**Base URL:** `http://localhost:8989/api/training`

**Endpoints:**

1. **POST /inject_data** - Inject single fault
```bash
curl -X POST http://localhost:8989/api/training/inject_data \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_path": "mining/crusher_1_bearing_temp",
    "value": 95.5,
    "duration_seconds": 60,
    "fault_type": "fixed_value"
  }'
```

2. **POST /inject_batch** - Inject multiple faults
```bash
curl -X POST http://localhost:8989/api/training/inject_batch \
  -H "Content-Type: application/json" \
  -d '{
    "faults": [
      {"sensor_path": "mining/crusher_1_bearing_temp", "value": 95.5, "duration_seconds": 60},
      {"sensor_path": "mining/crusher_1_vibration_x", "value": 22.0, "duration_seconds": 60}
    ]
  }'
```

3. **POST /upload_csv** - Upload CSV file
```bash
curl -X POST http://localhost:8989/api/training/upload_csv \
  -F "file=@telemetry_data.csv"
```

4. **POST /start_replay** - Start CSV replay
```bash
curl -X POST http://localhost:8989/api/training/start_replay \
  -H "Content-Type: application/json" \
  -d '{
    "speed_multiplier": 10.0
  }'
```

5. **POST /create_scenario** - Create training scenario
```bash
curl -X POST http://localhost:8989/api/training/create_scenario \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bearing Failure Progression",
    "description": "Gradual bearing temperature increase",
    "industry": "mining",
    "duration_seconds": 300,
    "difficulty": "intermediate",
    "tags": ["bearing", "temperature", "failure"],
    "injections": [
      {"at_second": 0, "sensor_path": "mining/crusher_1_bearing_temp", "value": 85},
      {"at_second": 120, "sensor_path": "mining/crusher_1_bearing_temp", "value": 95},
      {"at_second": 240, "sensor_path": "mining/crusher_1_bearing_temp", "value": 105}
    ]
  }'
```

6. **GET /scenarios** - List all scenarios
```bash
curl http://localhost:8989/api/training/scenarios
```

7. **POST /run_scenario** - Execute scenario
```bash
curl -X POST http://localhost:8989/api/training/run_scenario \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "scenario_1737293400",
    "trainee_id": "trainee_john_doe"
  }'
```

8. **POST /submit_diagnosis** - Submit trainee diagnosis
```bash
curl -X POST http://localhost:8989/api/training/submit_diagnosis \
  -H "Content-Type: application/json" \
  -d '{
    "trainee_id": "trainee_john_doe",
    "scenario_id": "scenario_1737293400",
    "diagnosis": "bearing_failure due to overheating"
  }'
```

9. **GET /leaderboard** - Get trainee rankings
```bash
curl http://localhost:8989/api/training/leaderboard
```

10. **GET /active_faults** - List active fault injections
```bash
curl http://localhost:8989/api/training/active_faults
```

### Sensor APIs

**GET /api/sensors** - List all sensors (optionally filter by industry)
```bash
curl http://localhost:8989/api/sensors?industry=mining
```

**GET /api/sensors/{sensor_path}** - Get specific sensor data
```bash
curl http://localhost:8989/api/sensors/mining/crusher_1_bearing_temp
```

---

## Container Management

### View Logs
```bash
# Follow logs in real-time
docker logs -f ot-simulator-1

# Show last 100 lines
docker logs --tail 100 ot-simulator-1

# Filter logs for specific keywords
docker logs ot-simulator-1 | grep -E "(Training API|Started|Error)"
```

### Container Status
```bash
# Check if container is running
docker ps | grep ot-simulator

# Show container resource usage
docker stats ot-simulator-1

# Inspect container details
docker inspect ot-simulator-1
```

### Stop and Restart
```bash
# Stop container
docker stop ot-simulator-1

# Start existing container
docker start ot-simulator-1

# Restart container
docker restart ot-simulator-1

# Stop and remove container
docker stop ot-simulator-1 && docker rm ot-simulator-1
```

### Execute Commands Inside Container
```bash
# Open shell in running container
docker exec -it ot-simulator-1 /bin/bash

# Check Python version
docker exec ot-simulator-1 python --version

# List processes
docker exec ot-simulator-1 ps aux

# Check network connectivity
docker exec ot-simulator-1 curl http://localhost:8989/api/health
```

---

## Troubleshooting

### Issue: Container Won't Start

**Symptom:** Container exits immediately after starting

**Solution:**
```bash
# Check logs for errors
docker logs ot-simulator-1

# Common issues:
# 1. Port conflicts - change host port mappings
# 2. Missing dependencies - rebuild image with --no-cache
# 3. Configuration errors - check config.yaml
```

### Issue: Port Already in Use

**Symptom:** `Error: port is already allocated`

**Solution:**
```bash
# Find process using the port (e.g., 8989)
lsof -i :8989

# Kill the process
kill -9 <PID>

# Or change port mapping
docker run -d --name ot-simulator-1 -p 9000:8989 ... ot-simulator:latest
# Access at http://localhost:9000
```

### Issue: Cannot Connect to Training Platform

**Symptom:** Web UI loads but Training Platform card is missing

**Solution:**
```bash
# Check container logs for errors
docker logs ot-simulator-1 | grep -i training

# Verify training_ui.py is included in image
docker exec ot-simulator-1 ls -la /app/ot_simulator/web_ui/training_ui.py

# Rebuild image if file is missing
docker build --no-cache -t ot-simulator:latest -f Dockerfile.simulator .
```

### Issue: API Returns 404 Not Found

**Symptom:** Training API endpoints return 404 errors

**Solution:**
```bash
# Verify Web UI is running
curl http://localhost:8989/api/health

# Check if training routes are registered
docker logs ot-simulator-1 | grep "Registered route"

# Verify correct URL format (include /api/training prefix)
curl http://localhost:8989/api/training/scenarios
```

### Issue: Fault Injection Doesn't Work

**Symptom:** Fault injection API succeeds but sensor values unchanged

**Solution:**
```bash
# Check if sensor path is correct (case-sensitive)
curl http://localhost:8989/api/sensors?industry=mining

# Verify fault is active
curl http://localhost:8989/api/training/active_faults

# Check container logs for errors
docker logs ot-simulator-1 | grep -i "fault"

# Ensure duration_seconds > 0
# Ensure protocol simulator is running (OPC-UA/MQTT/Modbus)
```

### Issue: Docker Socket Permission Denied

**Symptom:** `Cannot connect to the Docker daemon at unix://...`

**Solution:**
```bash
# Check if Colima is running
colima status

# Start Colima if stopped
colima start

# Verify Docker context
docker context ls
docker context use colima  # If not active

# Check socket permissions
ls -la /Users/pravin.varma/.colima/default/docker.sock

# Ensure user has access to docker group (macOS)
# Usually not needed with Colima, but verify:
groups
```

---

## Performance Optimization

### Resource Limits

Add resource limits to prevent container from consuming excessive resources:

```bash
docker run -d \
  --name ot-simulator-1 \
  --memory="2g" \
  --cpus="2.0" \
  -p 8989:8989 \
  -p 4840:4840 \
  -p 1883:1883 \
  -p 5020:5020 \
  ot-simulator:latest
```

### Image Size Optimization

Current image uses `python:3.11-slim` base (lightweight). To further reduce size:

```bash
# View image size
docker images ot-simulator

# Remove unused images
docker image prune -a
```

---

## Production Deployment

### Environment Variables

Pass configuration via environment variables:

```bash
docker run -d \
  --name ot-simulator-1 \
  -e LOG_LEVEL=INFO \
  -e WEB_UI_PORT=8989 \
  -e OPC_UA_PORT=4840 \
  -e MQTT_PORT=1883 \
  -e MODBUS_PORT=5020 \
  -p 8989:8989 \
  -p 4840:4840 \
  -p 1883:1883 \
  -p 5020:5020 \
  ot-simulator:latest
```

### Volume Mounts

Mount external directories for scenarios and logs:

```bash
docker run -d \
  --name ot-simulator-1 \
  -v /Users/pravin.varma/simulator_scenarios:/app/ot_simulator/scenarios \
  -v /Users/pravin.varma/simulator_logs:/app/logs \
  -p 8989:8989 \
  -p 4840:4840 \
  -p 1883:1883 \
  -p 5020:5020 \
  ot-simulator:latest
```

### Health Checks

Add Docker health check:

```bash
docker run -d \
  --name ot-simulator-1 \
  --health-cmd="curl -f http://localhost:8989/api/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  -p 8989:8989 \
  -p 4840:4840 \
  -p 1883:1883 \
  -p 5020:5020 \
  ot-simulator:latest
```

### Restart Policy

Auto-restart container on failure:

```bash
docker run -d \
  --name ot-simulator-1 \
  --restart unless-stopped \
  -p 8989:8989 \
  -p 4840:4840 \
  -p 1883:1883 \
  -p 5020:5020 \
  ot-simulator:latest
```

---

## Integration with Databricks

### Deploying to Databricks Apps

See `DATABRICKS_APPS_DEPLOYMENT.md` for complete Databricks deployment guide.

**Quick Summary:**

1. **Build and push image to container registry:**
```bash
# Tag for Databricks workspace container registry
docker tag ot-simulator:latest <workspace-url>.azurecr.io/ot-simulator:latest

# Push to registry
docker push <workspace-url>.azurecr.io/ot-simulator:latest
```

2. **Deploy via Databricks CLI:**
```bash
databricks apps deploy ot-simulator-app \
  --image <workspace-url>.azurecr.io/ot-simulator:latest \
  --port 8989
```

3. **Access via Databricks Apps URL:**
```
https://<workspace-url>/apps/<app-id>
```

---

## Multi-Instance Deployment

Run multiple simulator instances with different port mappings:

```bash
# Simulator 1
docker run -d --name ot-simulator-1 \
  -p 8989:8989 -p 4840:4840 -p 1883:1883 -p 5020:5020 \
  ot-simulator:latest

# Simulator 2 (different ports)
docker run -d --name ot-simulator-2 \
  -p 8990:8989 -p 4850:4840 -p 1893:1883 -p 5030:5020 \
  ot-simulator:latest

# Simulator 3 (different ports)
docker run -d --name ot-simulator-3 \
  -p 8991:8989 -p 4860:4840 -p 1903:1883 -p 5040:5020 \
  ot-simulator:latest
```

**Access:**
- Simulator 1: http://localhost:8989
- Simulator 2: http://localhost:8990
- Simulator 3: http://localhost:8991

---

## Summary

### Current Status
✅ Training Platform fully integrated into Web UI
✅ Dockerfile.simulator configured for container deployment
✅ All 10 training API endpoints functional
✅ Multi-protocol support (OPC-UA, MQTT, Modbus)
✅ Natural language interface operational
✅ Ready for production deployment

### Deployment Options
1. **Local Docker** - Use automated script or manual commands
2. **Docker Compose** - Multi-container orchestration
3. **Databricks Apps** - Cloud deployment with Unity Catalog integration

### Key Features
- 80 sensors across 4 industries (mining, utilities, manufacturing, oil & gas)
- 5 fault types (fixed_value, drift, spike, noise, stuck)
- Multi-step training scenarios with timed injections
- CSV data replay with variable speed (1x to 100x)
- Performance tracking and leaderboard
- Natural language interface powered by Claude Sonnet 4.5

### Support
- **User Guide:** [TRAINING_UI_USER_GUIDE.md](./TRAINING_UI_USER_GUIDE.md)
- **API Reference:** [TRAINING_API_NAVIGATION.md](./TRAINING_API_NAVIGATION.md)
- **Integration Status:** [GUI_TRAINING_INTEGRATION_STATUS.md](./GUI_TRAINING_INTEGRATION_STATUS.md)
- **Technical Summary:** [TRAINING_PLATFORM_SUMMARY.md](./TRAINING_PLATFORM_SUMMARY.md)
