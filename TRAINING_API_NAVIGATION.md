# Training Platform Navigation & Quick Reference

## Web UI URLs

### Local Development
- **Simulator 1**: http://localhost:8989
- **Simulator 2**: http://localhost:8990 (when running docker-compose.simulator2.yml)
- **Simulator 3**: http://localhost:8991 (when running docker-compose.simulator3.yml)

### Docker Containers (after rebuild)
Each simulator container will have its own web UI with training API:
- **Container 1**: http://localhost:8989 (inside: port 8989)
- **Container 2**: http://localhost:8990 (inside: port 8989)
- **Container 3**: http://localhost:8991 (inside: port 8989)

---

## Training API Endpoints

### Base URL
```
http://localhost:8989/api/training
```

### 1. Manual Data Injection

#### Inject Single Sensor Value
```bash
POST /api/training/inject_data

curl -X POST http://localhost:8989/api/training/inject_data \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_path": "mining/crusher_bearing_temp",
    "value": 95.5,
    "duration_seconds": 60
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Injected value 95.5 to mining/crusher_bearing_temp",
  "sensor_path": "mining/crusher_bearing_temp",
  "value": 95.5,
  "duration_seconds": 60
}
```

---

#### Inject Multiple Sensors (Batch)
```bash
POST /api/training/inject_batch

curl -X POST http://localhost:8989/api/training/inject_batch \
  -H "Content-Type: application/json" \
  -d '{
    "injections": [
      {"sensor_path": "mining/crusher_bearing_temp", "value": 95.5, "duration_seconds": 60},
      {"sensor_path": "mining/crusher_vibration", "value": 8.2, "duration_seconds": 60}
    ]
  }'
```

---

### 2. Fault Scenarios

#### List All Scenarios
```bash
GET /api/training/scenarios

# All scenarios
curl http://localhost:8989/api/training/scenarios

# Filter by industry
curl http://localhost:8989/api/training/scenarios?industry=mining

# Filter by difficulty
curl http://localhost:8989/api/training/scenarios?difficulty=beginner
```

**Response**:
```json
{
  "success": true,
  "scenarios": [
    {
      "scenario_id": "scenario_1737293400",
      "name": "Bearing Overheating Scenario",
      "description": "Gradual bearing temperature increase",
      "industry": "mining",
      "duration_seconds": 300,
      "difficulty": "intermediate",
      "tags": ["bearing", "temperature", "failure"],
      "injections": [...]
    }
  ],
  "total": 1
}
```

---

#### Create New Scenario
```bash
POST /api/training/create_scenario

curl -X POST http://localhost:8989/api/training/create_scenario \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bearing Overheating Scenario",
    "description": "Gradual bearing temperature increase leading to failure",
    "industry": "mining",
    "duration_seconds": 300,
    "difficulty": "intermediate",
    "tags": ["bearing", "temperature", "failure"],
    "injections": [
      {"sensor_path": "mining/crusher_bearing_temp", "value": 85, "at_second": 0},
      {"sensor_path": "mining/crusher_bearing_temp", "value": 95, "at_second": 120},
      {"sensor_path": "mining/crusher_bearing_temp", "value": 105, "at_second": 240}
    ]
  }'
```

**Response**:
```json
{
  "success": true,
  "scenario_id": "scenario_1737293400",
  "scenario": {
    "scenario_id": "scenario_1737293400",
    "name": "Bearing Overheating Scenario",
    ...
  }
}
```

---

#### Run Saved Scenario
```bash
POST /api/training/run_scenario

curl -X POST http://localhost:8989/api/training/run_scenario \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "scenario_1737293400",
    "trainee_id": "trainee_john_doe"
  }'
```

**Response**:
```json
{
  "success": true,
  "scenario_id": "scenario_1737293400",
  "trainee_id": "trainee_john_doe",
  "message": "Scenario 'Bearing Overheating Scenario' started",
  "duration_seconds": 300
}
```

---

### 3. CSV Data Replay

#### Upload CSV File
```bash
POST /api/training/upload_csv

# Create sample CSV
cat > telemetry.csv <<EOF
timestamp,sensor_path,value
2025-01-19T10:00:00,mining/crusher_bearing_temp,75.5
2025-01-19T10:00:01,mining/crusher_bearing_temp,76.2
2025-01-19T10:00:02,mining/crusher_bearing_temp,77.1
EOF

# Upload
curl -X POST http://localhost:8989/api/training/upload_csv \
  -F "file=@telemetry.csv"
```

**Response**:
```json
{
  "success": true,
  "replay_id": "replay_1737293400000",
  "rows_loaded": 3,
  "message": "CSV uploaded successfully with 3 rows"
}
```

---

#### Start CSV Replay
```bash
POST /api/training/start_replay

# Real-time speed (1x)
curl -X POST http://localhost:8989/api/training/start_replay \
  -H "Content-Type: application/json" \
  -d '{
    "replay_id": "replay_1737293400000",
    "speed": 1.0
  }'

# Fast forward 10x
curl -X POST http://localhost:8989/api/training/start_replay \
  -H "Content-Type: application/json" \
  -d '{
    "replay_id": "replay_1737293400000",
    "speed": 10.0
  }'
```

---

### 4. Training Assessment

#### Submit Diagnosis
```bash
POST /api/training/submit_diagnosis

curl -X POST http://localhost:8989/api/training/submit_diagnosis \
  -H "Content-Type: application/json" \
  -d '{
    "trainee_id": "trainee_john_doe",
    "scenario_id": "scenario_1737293400",
    "diagnosis": "bearing_failure due to overheating",
    "actions": [
      {"action": "viewed_chart", "sensor": "bearing_temp", "timestamp": 1737293450},
      {"action": "checked_vibration", "sensor": "vibration", "timestamp": 1737293460}
    ]
  }'
```

**Response**:
```json
{
  "success": true,
  "assessment": {
    "trainee_id": "trainee_john_doe",
    "scenario_id": "scenario_1737293400",
    "diagnosis": "bearing_failure due to overheating",
    "correct": true,
    "score": 100.0,
    "time_to_diagnose": 10.0
  },
  "message": "Diagnosis submitted successfully"
}
```

---

#### Get Leaderboard
```bash
GET /api/training/leaderboard

# All trainees
curl http://localhost:8989/api/training/leaderboard

# Specific scenario
curl http://localhost:8989/api/training/leaderboard?scenario_id=scenario_1737293400
```

**Response**:
```json
{
  "success": true,
  "leaderboard": [
    {
      "trainee_id": "trainee_john_doe",
      "total_score": 100,
      "attempts": 1,
      "correct": 1,
      "avg_score": 100.0,
      "avg_time": 10.0,
      "accuracy": 100.0
    }
  ],
  "total_trainees": 1
}
```

---

### 5. Legacy Compatibility

#### Legacy Fault Injection (for NL Interface)
```bash
POST /api/fault/inject

curl -X POST http://localhost:8989/api/fault/inject \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_path": "mining/crusher_bearing_temp",
    "duration": 60
  }'
```

---

## Natural Language Commands

The simulator has an integrated natural language interface powered by Claude Sonnet 4.5 (via Databricks Foundation Model APIs).

### Example Commands:

```
"inject fault into bearing temperature sensor for 60 seconds"
"simulate hydraulic pump failure"
"show me all temperature sensors in the mining industry"
"start a training scenario for bearing failure"
"what's the status of all simulators?"
```

---

## Sensor Paths Reference

### Format
```
{industry}/{sensor_name}
```

### Available Industries
- `mining`
- `utilities`
- `manufacturing`
- `oil_gas`
- `aerospace`
- `space`
- `water_wastewater`
- `electric_power`
- `automotive`
- `chemical`
- `food_beverage`
- `pharmaceutical`
- `data_center`
- `smart_building`
- `agriculture`
- `renewable_energy`

### Example Sensor Paths
```
mining/crusher_bearing_temp
mining/crusher_vibration
utilities/pump_flow_rate
manufacturing/press_force
oil_gas/wellhead_pressure
automotive/weld_current
```

---

## Web UI Features

### Main Dashboard
- **URL**: http://localhost:8989
- Real-time sensor data visualization
- Chart.js graphs with 500ms updates
- WebSocket streaming
- Natural language chat interface

### Training Tab (Coming Soon)
- Scenario browser
- CSV upload interface
- Training assessment view
- Leaderboard display

### Sensor Browser
- Browse all 379 sensors
- Filter by industry
- Filter by PLC
- Create charts from sensor selection

---

## Quick Start Scripts

### Test All Training APIs
```bash
#!/bin/bash
BASE_URL="http://localhost:8989"

echo "1. Inject single fault..."
curl -X POST $BASE_URL/api/training/inject_data \
  -H "Content-Type: application/json" \
  -d '{"sensor_path": "mining/crusher_bearing_temp", "value": 95.5, "duration_seconds": 60}'

echo -e "\n\n2. Create scenario..."
SCENARIO_ID=$(curl -X POST $BASE_URL/api/training/create_scenario \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Scenario",
    "description": "Test bearing failure",
    "industry": "mining",
    "duration_seconds": 60,
    "difficulty": "beginner",
    "tags": ["bearing", "test"],
    "injections": [
      {"sensor_path": "mining/crusher_bearing_temp", "value": 85, "at_second": 0}
    ]
  }' | jq -r '.scenario_id')

echo "Created scenario: $SCENARIO_ID"

echo -e "\n\n3. List scenarios..."
curl $BASE_URL/api/training/scenarios

echo -e "\n\n4. Run scenario..."
curl -X POST $BASE_URL/api/training/run_scenario \
  -H "Content-Type: application/json" \
  -d "{
    \"scenario_id\": \"$SCENARIO_ID\",
    \"trainee_id\": \"test_trainee\"
  }"

echo -e "\n\n5. Submit diagnosis..."
curl -X POST $BASE_URL/api/training/submit_diagnosis \
  -H "Content-Type: application/json" \
  -d "{
    \"trainee_id\": \"test_trainee\",
    \"scenario_id\": \"$SCENARIO_ID\",
    \"diagnosis\": \"bearing failure\"
  }"

echo -e "\n\n6. Get leaderboard..."
curl $BASE_URL/api/training/leaderboard
```

---

## Docker Commands

### Rebuild Simulator with Web UI
```bash
# Stop existing containers
docker-compose -f docker-compose.simulator1.yml down

# Rebuild with new Dockerfile (includes --web-ui flag)
docker-compose -f docker-compose.simulator1.yml build --no-cache

# Start with web UI
docker-compose -f docker-compose.simulator1.yml up -d

# Check logs
docker logs -f ot-simulator-1

# Access web UI
open http://localhost:8989
```

### Run All 3 Simulators with Web UIs
```bash
# Start all 3 simulators
docker-compose -f docker-compose.simulator1.yml up -d
docker-compose -f docker-compose.simulator2.yml up -d
docker-compose -f docker-compose.simulator3.yml up -d

# Access web UIs
open http://localhost:8989   # Simulator 1
open http://localhost:8990   # Simulator 2
open http://localhost:8991   # Simulator 3
```

---

## Documentation Links

### Training Platform Docs
- **Implementation Guide**: [TRAINING_PLATFORM_IMPLEMENTATION.md](./TRAINING_PLATFORM_IMPLEMENTATION.md)
- **Databricks Value Proposition**: [DATABRICKS_TRAINING_PLATFORM_VALUE.md](./DATABRICKS_TRAINING_PLATFORM_VALUE.md)
- **Use Case Example**: [TRAINING_USE_CASE_JOHN_DEERE.md](./TRAINING_USE_CASE_JOHN_DEERE.md)
- **Natural Language Guide**: [TRAINING_NL_INTERFACE_GUIDE.md](./TRAINING_NL_INTERFACE_GUIDE.md)
- **Manual Injection Guide**: [MANUAL_DATA_INJECTION_GUIDE.md](./MANUAL_DATA_INJECTION_GUIDE.md)
- **Complete Solution**: [TRAINING_PLATFORM_COMPLETE_SOLUTION.md](./TRAINING_PLATFORM_COMPLETE_SOLUTION.md)

### Technical Docs
- **Docker Setup**: [DOCKER_SIMULATORS.md](./DOCKER_SIMULATORS.md)
- **Protocol Support**: [PROTOCOLS.md](./PROTOCOLS.md)
- **Tag Normalization**: [TAG_NORMALIZATION_IMPLEMENTATION.md](./TAG_NORMALIZATION_IMPLEMENTATION.md)
- **ZeroBus Integration**: [ZEROBUS_NORMALIZED_TAGS_GUIDE.md](./ZEROBUS_NORMALIZED_TAGS_GUIDE.md)

---

## Support

For issues or questions:
1. Check logs: `docker logs ot-simulator-1`
2. Test health endpoint: `curl http://localhost:8989/api/health`
3. Review documentation in project root
4. Check simulator status: `docker ps -a --filter "name=simulator"`

---

## Summary

The training platform provides:
- ✅ 10 REST API endpoints for training operations
- ✅ Natural language interface via Claude Sonnet 4.5
- ✅ Real-time web UI with charts and WebSocket streaming
- ✅ Fault scenario management (create, save, load, run)
- ✅ CSV data upload and replay (1x to 100x speed)
- ✅ Training assessment and leaderboard
- ✅ 379 sensors across 16 industries
- ✅ 3 protocols (OPC-UA, MQTT, Modbus)
- ✅ Integration with Databricks (ZeroBus, Unity Catalog, Foundation Models)

**Ready for production deployment and pilot testing with 20 trainees!**
