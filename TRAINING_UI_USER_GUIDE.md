# Training Platform UI - User Guide

## Overview

The Training Platform provides a visual interface for creating training scenarios, injecting faults, and assessing operator performance. Access it via the main web UI at http://localhost:8989.

---

## Accessing the Training Platform

### Step 1: Open Web UI
Navigate to: `http://localhost:8989`

### Step 2: Expand Training Platform
Click on the **"🎯 Training Platform"** card header to expand the training interface.

The card will expand to show 4 tabs:
1. **Inject Faults** - Manual fault injection
2. **Scenarios** - Multi-step training scenarios
3. **CSV Upload** - Historical data replay
4. **Leaderboard** - Performance tracking

---

## Tab 1: Inject Faults

### Single Fault Injection

**Use Case**: Inject a specific value into a sensor for testing or training.

**Fields**:
- **Sensor Path**: The sensor to inject into (e.g., `mining/crusher_1_bearing_temp`)
- **Value**: The value to inject (e.g., `95.5`)
- **Duration (seconds)**: How long to maintain the injected value (e.g., `60`)
- **Fault Type**: Select from dropdown:
  - `fixed_value` - Override with constant value
  - `drift` - Add gradual drift to normal readings
  - `spike` - Sudden spike above normal
  - `noise` - Add random noise to readings
  - `stuck` - Freeze at current value

**Example**:
```
Sensor Path: mining/crusher_1_bearing_temp
Value: 95.5
Duration: 60 seconds
Fault Type: fixed_value
```

**Action**: Click **"Inject Fault"** button.

**Result**: The sensor will report 95.5°C for the next 60 seconds, overriding its normal simulated value.

---

### Batch Fault Injection

**Use Case**: Inject multiple faults simultaneously (e.g., simulate cascading failure).

**How to Use**:
1. Click **"+ Add Fault"** to add a new fault to the list
2. Fill in sensor path, value, duration for each fault
3. Click **"Inject All Faults"** to execute all at once

**Example Batch**:
```
Fault 1: mining/crusher_1_bearing_temp = 95.5 (60s)
Fault 2: mining/crusher_1_vibration_x = 22.0 (60s)
Fault 3: mining/crusher_1_oil_pressure = 1.5 (60s)
```

**Use Case**: Simulate bearing failure with correlated sensor anomalies.

---

## Tab 2: Scenarios

### Viewing Existing Scenarios

The **Scenarios** tab displays all saved training scenarios in a grid layout.

**Each scenario card shows**:
- **Name**: Descriptive scenario name
- **Description**: What the scenario simulates
- **Industry**: Target industry (mining, utilities, etc.)
- **Duration**: Total scenario runtime
- **Difficulty**: Beginner, Intermediate, or Advanced
- **Tags**: Keywords for searching (e.g., "bearing", "temperature", "failure")

**Actions**:
- **Run Scenario**: Start the scenario immediately
- **Edit**: Modify scenario details
- **Delete**: Remove scenario

---

### Creating a New Scenario

**Step 1**: Click **"Create New Scenario"** button

**Step 2**: Fill in scenario metadata:
- **Scenario Name**: `Bearing Overheating Failure`
- **Description**: `Gradual bearing temperature increase leading to failure`
- **Industry**: `mining`
- **Duration**: `300` seconds (5 minutes)
- **Difficulty**: `intermediate`
- **Tags**: `bearing, temperature, failure`

**Step 3**: Add timed injections:

Click **"+ Add Injection"** for each fault event:

```
Injection 1:
  At Second: 0
  Sensor: mining/crusher_1_bearing_temp
  Value: 85
  Fault Type: fixed_value

Injection 2:
  At Second: 120
  Sensor: mining/crusher_1_bearing_temp
  Value: 95
  Fault Type: fixed_value

Injection 3:
  At Second: 240
  Sensor: mining/crusher_1_bearing_temp
  Value: 105
  Fault Type: fixed_value
```

**Step 4**: Click **"Save Scenario"**

**Result**: The scenario is saved to `ot_simulator/scenarios/` directory and appears in the scenarios list.

---

### Running a Scenario

**Step 1**: Click **"Run Scenario"** on any scenario card

**Step 2**: Enter trainee ID:
```
Trainee ID: trainee_john_doe
```

**Step 3**: Click **"Start"**

**Result**: The scenario executes automatically. Faults are injected at the specified times. Trainees must diagnose the problem within the scenario duration.

---

## Tab 3: CSV Upload

### Use Case

Replay historical telemetry data for training. Upload CSV files containing real sensor data from past incidents.

---

### CSV Format

**Required Columns**:
```csv
timestamp,sensor_path,value
2025-01-19T10:00:00,mining/crusher_1_bearing_temp,75.5
2025-01-19T10:00:01,mining/crusher_1_bearing_temp,76.2
2025-01-19T10:00:02,mining/crusher_1_bearing_temp,77.1
```

**Supported Formats**:
- **ISO 8601 timestamps**: `2025-01-19T10:00:00`
- **Unix timestamps**: `1737280800`
- **Relative timestamps**: `0, 1, 2, 3...` (seconds from start)

---

### Uploading CSV

**Step 1**: Drag CSV file onto the drop zone OR click **"Choose File"**

**Step 2**: Preview appears showing:
- Number of rows loaded
- Time range (first → last timestamp)
- Sensors affected
- Sample data (first 10 rows)

**Step 3**: Set replay speed:
```
Speed: 1.0x (real-time)
Speed: 10.0x (10x faster)
Speed: 100.0x (100x faster)
```

**Step 4**: Click **"Start Replay"**

**Result**: Sensor values are injected according to the CSV timestamps and selected speed multiplier.

---

### Example Use Case

**Scenario**: You have a CSV export from a real bearing failure incident on 2024-12-15.

**Steps**:
1. Upload `bearing_failure_2024_12_15.csv` (2,500 rows, 30-minute incident)
2. Set speed to `100.0x` (replay 30 minutes in 18 seconds)
3. Start replay
4. Trainees watch the failure unfold in accelerated time

**Training Value**: Trainees experience real-world failure patterns without waiting 30 minutes.

---

## Tab 4: Leaderboard

### Overview

The Leaderboard tracks trainee performance across all scenarios.

**Metrics Displayed**:
- **Trainee ID**: Unique identifier
- **Total Score**: Cumulative points
- **Attempts**: Number of scenarios attempted
- **Correct**: Number of correct diagnoses
- **Average Score**: Mean score per attempt
- **Average Time**: Mean time to diagnose (seconds)
- **Accuracy**: Percentage of correct diagnoses

---

### Submitting a Diagnosis

**During a scenario**, trainees can submit their diagnosis via:

**Method 1: REST API**
```bash
curl -X POST http://localhost:8989/api/training/submit_diagnosis \
  -H "Content-Type: application/json" \
  -d '{
    "trainee_id": "trainee_john_doe",
    "scenario_id": "scenario_1737293400",
    "diagnosis": "bearing_failure due to overheating"
  }'
```

**Method 2: Natural Language Chat**
```
"submit diagnosis: bearing failure due to overheating"
```

**Method 3: Diagnosis Form** (if implemented in future enhancement)

---

### Leaderboard Rankings

**Sorting**: By default, sorted by **Total Score** (descending).

**Example Leaderboard**:
```
Rank | Trainee ID       | Total Score | Attempts | Correct | Avg Score | Avg Time | Accuracy
-----|------------------|-------------|----------|---------|-----------|----------|----------
1    | trainee_alice    | 450         | 5        | 5       | 90.0      | 8.5s     | 100%
2    | trainee_bob      | 380         | 5        | 4       | 76.0      | 12.3s    | 80%
3    | trainee_charlie  | 320         | 4        | 3       | 80.0      | 15.1s    | 75%
```

**Filtering**: Click on scenario name to filter leaderboard by specific scenario.

---

## Natural Language Integration

### Alternative to GUI

All training functions can be executed via natural language commands in the **Operations AI Assistant** chat panel.

**Example Commands**:

```
"inject fault into mining crusher bearing temperature sensor for 60 seconds"
"set mining crusher vibration to 22 for 30 seconds"
"create a training scenario for bearing failure"
"show me all temperature sensors"
"start scenario scenario_1737293400 for trainee john_doe"
"submit diagnosis: bearing failure due to overheating"
"show me the leaderboard"
```

**How to Access**:
1. Click **"🤖 Operations AI Assistant"** button (bottom right)
2. Type your command in plain English
3. Press **Send**

The LLM agent (Claude Sonnet 4.5) interprets your intent and calls the appropriate training API.

---

## REST API Reference

For programmatic access, all training features are available via REST API.

**Base URL**: `http://localhost:8989/api/training`

### Endpoints:

1. **POST** `/inject_data` - Inject single fault
2. **POST** `/inject_batch` - Inject multiple faults
3. **POST** `/upload_csv` - Upload CSV file
4. **POST** `/start_replay` - Start CSV replay
5. **POST** `/create_scenario` - Create new scenario
6. **GET** `/scenarios` - List all scenarios
7. **POST** `/run_scenario` - Execute scenario
8. **POST** `/submit_diagnosis` - Submit trainee diagnosis
9. **GET** `/leaderboard` - Get trainee rankings
10. **POST** `/api/fault/inject` - Legacy fault endpoint (backward compatibility)

**Complete API documentation**: See `TRAINING_API_NAVIGATION.md`

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Click card header** | Expand/collapse Training Platform |
| **Tab** | Navigate between form fields |
| **Enter** | Submit current form |
| **Esc** | Close modals |

---

## Tips & Best Practices

### For Trainers:

1. **Start with simple scenarios**: Use "beginner" difficulty for initial training
2. **Gradually increase complexity**: Move to multi-sensor faults once basics are mastered
3. **Use real CSV data**: Export actual incident data for most realistic training
4. **Review leaderboard regularly**: Identify trainees who need additional support

### For Trainees:

1. **Watch all related sensors**: Bearing failures affect temperature, vibration, and oil pressure
2. **Note timing**: Fast diagnosis earns higher scores
3. **Use the sensor browser**: Explore what sensors are available before starting scenarios
4. **Ask for help**: Use natural language chat to query sensor information

### For Administrators:

1. **Create scenario library**: Build 20-30 scenarios covering common failure modes
2. **Tag scenarios consistently**: Use consistent tags for easier searching
3. **Back up scenarios**: Scenarios are saved in `ot_simulator/scenarios/` directory
4. **Monitor API usage**: Check logs for trainee activity patterns

---

## Troubleshooting

### Issue: "Sensor not found" error

**Cause**: Invalid sensor path

**Solution**: Use the sensor browser or call `/api/sensors` to get valid sensor paths.

**Example**:
```bash
curl http://localhost:8989/api/sensors?industry=mining
```

### Issue: Fault injection doesn't seem to work

**Cause**: Duration expired or sensor path case-sensitive mismatch

**Solution**:
1. Check sensor path exactly matches (case-sensitive)
2. Verify duration > 0
3. Check fault is still active: `/api/training/active_faults`

### Issue: CSV replay too fast/slow

**Cause**: Incorrect speed multiplier

**Solution**: Adjust speed parameter:
- `1.0` = real-time
- `10.0` = 10x faster
- `0.5` = half speed (slow motion)

### Issue: Leaderboard empty

**Cause**: No diagnoses submitted yet

**Solution**: Submit at least one diagnosis via API or natural language chat.

---

## Advanced Features

### Custom Fault Types

Beyond `fixed_value`, use advanced fault types:

**Drift Fault**:
```json
{
  "sensor_path": "mining/crusher_1_bearing_temp",
  "fault_type": "drift",
  "params": {"drift": 0.5},
  "duration_seconds": 300
}
```
Result: Adds +0.5°C to every reading for 5 minutes

**Noise Fault**:
```json
{
  "sensor_path": "mining/crusher_1_bearing_temp",
  "fault_type": "noise",
  "params": {"amplitude": 5},
  "duration_seconds": 120
}
```
Result: Adds random noise (±5°C) to every reading for 2 minutes

**Stuck Fault**:
```json
{
  "sensor_path": "mining/crusher_1_bearing_temp",
  "fault_type": "stuck",
  "params": {},
  "duration_seconds": 60
}
```
Result: Freezes sensor at current value for 1 minute

---

## Integration with Databricks

### ZeroBus Streaming

Training events can be streamed to Delta Lake for analysis:

**Tables**:
- `main.training.fault_injections` - All fault injection events
- `main.training.scenario_executions` - Scenario runs
- `main.training.trainee_diagnoses` - Submitted diagnoses
- `main.training.leaderboard` - Real-time rankings

**ML Integration**:
- Train ML models on fault patterns
- Predict trainee performance
- Recommend personalized training scenarios

### Foundation Model APIs

The natural language interface uses **Databricks Foundation Model APIs** (Claude Sonnet 4.5) for:
- Intent recognition
- Context-aware responses
- Scenario generation from descriptions
- Automated grading of text diagnoses

---

## Summary

The Training Platform provides three access methods:

1. **GUI**: Visual interface for creating scenarios, injecting faults, uploading CSV files, and viewing leaderboard
2. **REST API**: Programmatic access for automation and integration
3. **Natural Language**: Plain English commands for intuitive interaction

All methods provide the same functionality - choose based on user preference and use case.

**Getting Started**:
1. Open http://localhost:8989
2. Click "🎯 Training Platform"
3. Explore the 4 tabs
4. Try injecting a simple fault to see it work!

**Support**: See `TRAINING_API_NAVIGATION.md` for complete API reference and troubleshooting.
