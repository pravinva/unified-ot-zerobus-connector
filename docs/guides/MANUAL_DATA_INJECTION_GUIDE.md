# Manual Data Injection & Custom Fault Creation Guide

## Overview

While the simulator can automatically generate realistic sensor data, **trainees and instructors can manually inject custom data and faults** to create specific test scenarios, replay real-world incidents, or test edge cases.

This is crucial for:
- **Recreating actual field failures** from customer equipment
- **Testing diagnostic skills** with known fault patterns
- **Creating certification exam scenarios** with precise parameters
- **Validating ML models** with controlled test data

---

## Methods of Manual Data Injection

### Method 1: Direct API Injection (REST)

#### Inject Single Data Point

```bash
# Inject a single sensor reading
curl -X POST http://localhost:8989/api/simulator/inject_data \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "8R_training_001",
    "sensor": "hydraulic_pressure",
    "value": 2850,
    "timestamp": "2026-01-19T15:30:00Z",
    "quality": "good"
  }'
```

#### Inject Batch of Data Points

```bash
# Inject historical replay data
curl -X POST http://localhost:8989/api/simulator/inject_batch \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "8R_training_001",
    "data_points": [
      {
        "sensor": "hydraulic_pressure",
        "value": 3000,
        "timestamp": "2026-01-19T15:00:00Z"
      },
      {
        "sensor": "hydraulic_pressure",
        "value": 2950,
        "timestamp": "2026-01-19T15:05:00Z"
      },
      {
        "sensor": "hydraulic_pressure",
        "value": 2900,
        "timestamp": "2026-01-19T15:10:00Z"
      },
      {
        "sensor": "hydraulic_pressure",
        "value": 2850,
        "timestamp": "2026-01-19T15:15:00Z"
      }
    ]
  }'
```

---

### Method 2: Natural Language Commands

#### Simple Fault Injection

```
Trainee: "Set hydraulic pressure to 2700 PSI for the next 5 minutes"

System: ✓ Manual override activated

        Equipment: 8R_training_001
        Sensor: hydraulic_pressure
        Current value: 3000 PSI
        Override value: 2700 PSI
        Duration: 5 minutes

        Override active. Type "stop override" to cancel.

---

Trainee: "Gradually decrease engine RPM from 2100 to 1800 over 10 minutes"

System: ✓ Gradual sensor modification configured

        Equipment: 8R_training_001
        Sensor: engine_rpm
        Start value: 2100 RPM
        End value: 1800 RPM
        Duration: 10 minutes
        Profile: Linear decline

        Modification in progress. Real-time data streaming to Databricks.

---

Trainee: "Make the oil pressure fluctuate randomly between 40 and 60 PSI"

System: ✓ Random fluctuation pattern applied

        Equipment: 8R_training_001
        Sensor: oil_pressure
        Range: 40-60 PSI
        Pattern: Random walk with ±5 PSI steps
        Update frequency: Every 2 seconds

        This simulates a failing oil pressure sensor or regulator.
        Duration: Continuous until stopped
```

#### Complex Multi-Sensor Scenarios

```
Trainee: "Create a scenario where:
         - Coolant temp increases from 180 to 240°F over 15 minutes
         - Engine power decreases proportionally (340 HP to 280 HP)
         - Fan speed increases to 100%
         - Keep all other sensors normal"

System: ✓ Complex multi-sensor scenario created

        Scenario Name: overheating_simulation_001
        Equipment: 8R_training_001

        Sensor modifications:
        1. coolant_temp: 180→240°F (15 min, +4°F/min)
        2. engine_power: 340→280 HP (15 min, -4 HP/min)
        3. fan_speed: 0→100% (immediate, then hold)
        4. All other sensors: Normal operation

        Realistic interactions enabled:
        • Higher coolant temp → Slight fuel efficiency loss
        • Lower power → Reduced hydraulic flow (indirect)
        • High fan speed → Slight engine load increase

        Scenario active. Say "save scenario" to reuse later.
```

---

### Method 3: CSV File Upload

#### Upload Historical Data from Real Equipment

**CSV Format:**
```csv
timestamp,equipment_id,sensor_name,value,quality
2026-01-15T08:00:00Z,8R_field_unit_042,hydraulic_pressure,3000,good
2026-01-15T08:00:01Z,8R_field_unit_042,hydraulic_pressure,2998,good
2026-01-15T08:00:02Z,8R_field_unit_042,hydraulic_pressure,2995,good
2026-01-15T08:00:03Z,8R_field_unit_042,hydraulic_pressure,2990,good
...
```

**Upload via Web UI:**
```
1. Go to http://localhost:8989/training
2. Click "Upload Historical Data"
3. Select CSV file
4. Map columns (timestamp → timestamp, sensor_name → sensor, etc.)
5. Click "Import and Replay"
```

**Upload via API:**
```bash
curl -X POST http://localhost:8989/api/simulator/upload_csv \
  -F "file=@real_failure_data.csv" \
  -F "equipment_id=8R_training_replay" \
  -F "replay_speed=1.0"  # 1.0 = real-time, 10.0 = 10x speed
```

**Natural Language Upload:**
```
Instructor: "Upload the CSV file from the disk failure last month and
            replay it at 5x speed for training"

System: ✓ CSV file loaded: /data/failures/202512_bearing_failure.csv

        Data summary:
        • 50,000 data points
        • Duration: 24 hours (will replay in 4.8 hours at 5x)
        • Equipment: 8R_field_unit_042
        • Fault: Bearing failure progression
        • Sensors: 12 (vibration, temp, pressure, etc.)

        Replay starting...
        Trainees can observe the failure develop in compressed time.
```

---

### Method 4: Python SDK (For Advanced Users)

#### Manual Data Injection via Python

```python
from simulator_client import SimulatorClient

# Connect to simulator
sim = SimulatorClient(host="localhost", port=8989)

# Inject single value
sim.inject_sensor_value(
    equipment_id="8R_training_001",
    sensor="hydraulic_pressure",
    value=2850,
    timestamp="2026-01-19T15:30:00Z",
    quality="good"
)

# Inject time series
import pandas as pd
import numpy as np

# Create synthetic fault pattern
timestamps = pd.date_range("2026-01-19 15:00:00", periods=60, freq="1min")
pressures = np.linspace(3000, 2700, 60)  # Gradual decline

for ts, press in zip(timestamps, pressures):
    sim.inject_sensor_value(
        equipment_id="8R_training_001",
        sensor="hydraulic_pressure",
        value=float(press),
        timestamp=ts.isoformat(),
        quality="good"
    )

print("✓ Injected 60 minutes of declining pressure data")
```

#### Replay Real JDLink Telemetry

```python
from simulator_client import SimulatorClient
import pandas as pd

# Load real telemetry from JDLink export
df = pd.read_csv("jdlink_export_8R_failure_20251215.csv")

# Initialize simulator
sim = SimulatorClient()

# Replay at 10x speed
for _, row in df.iterrows():
    sim.inject_sensor_value(
        equipment_id="8R_training_replay",
        sensor=row['sensor_name'],
        value=row['value'],
        timestamp=row['timestamp'],
        quality=row['quality']
    )

    # Sleep 0.1 seconds (10x speed)
    time.sleep(0.1)

print(f"✓ Replayed {len(df)} real data points from field failure")
```

---

### Method 5: SQL Injection (Direct to Databricks)

#### Inject Test Data Directly into Delta Table

```sql
-- Inject a specific fault pattern for training
INSERT INTO main.training.equipment_telemetry
VALUES
  ('8R_training_001', 'hydraulic_pressure', 3000, 'good', TIMESTAMP '2026-01-19 15:00:00'),
  ('8R_training_001', 'hydraulic_pressure', 2950, 'good', TIMESTAMP '2026-01-19 15:05:00'),
  ('8R_training_001', 'hydraulic_pressure', 2900, 'good', TIMESTAMP '2026-01-19 15:10:00'),
  ('8R_training_001', 'hydraulic_pressure', 2850, 'good', TIMESTAMP '2026-01-19 15:15:00'),
  ('8R_training_001', 'hydraulic_pressure', 2800, 'good', TIMESTAMP '2026-01-19 15:20:00'),
  ('8R_training_001', 'hydraulic_pressure', 2750, 'good', TIMESTAMP '2026-01-19 15:25:00'),
  ('8R_training_001', 'hydraulic_pressure', 2700, 'bad', TIMESTAMP '2026-01-19 15:30:00');

-- Create a complex multi-sensor fault scenario
INSERT INTO main.training.equipment_telemetry
SELECT
  '8R_training_complex' as equipment_id,
  sensor_name,
  sensor_value,
  'good' as quality,
  event_time
FROM (
  -- Normal operation for 5 minutes
  SELECT 'engine_rpm' as sensor_name, 2100 as sensor_value, timestamp_add(TIMESTAMP '2026-01-19 15:00:00', interval (id * 10) seconds) as event_time
  FROM range(30)  -- 30 readings at 10-second intervals = 5 minutes

  UNION ALL

  -- Gradual RPM decline (simulating fuel pump failure)
  SELECT 'engine_rpm', 2100 - (id * 10), timestamp_add(TIMESTAMP '2026-01-19 15:05:00', interval (id * 10) seconds)
  FROM range(30)  -- RPM drops from 2100 to 1800

  UNION ALL

  -- Fuel pressure drops
  SELECT 'fuel_pressure', 50 - (id * 0.5), timestamp_add(TIMESTAMP '2026-01-19 15:05:00', interval (id * 10) seconds)
  FROM range(30)  -- Fuel pressure 50→35 PSI
);
```

#### Load External Dataset

```sql
-- Load real failure data from CSV stored in DBFS
COPY INTO main.training.equipment_telemetry
FROM '/dbfs/training_data/real_failures/202512_bearing_failure.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true');

-- Verify loaded data
SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
FROM main.training.equipment_telemetry
WHERE equipment_id = '8R_field_unit_042';
```

---

## Creating Custom Fault Libraries

### Save Reusable Fault Patterns

#### Via Natural Language

```
Instructor: "Save the current hydraulic leak scenario as a reusable template"

System: ✓ Fault pattern saved

        Template Name: hydraulic_leak_gradual
        Template ID: FAULT_TEMPLATE_001

        Parameters:
        • Sensor: hydraulic_pressure
        • Start value: 3000 PSI
        • End value: 2700 PSI
        • Duration: 30 minutes
        • Profile: Linear decline with ±20 PSI noise

        Usage:
        "Apply hydraulic_leak_gradual to equipment 8R_training_002"

---

Instructor: "Create a fault library for bearing failures with 5 severity levels"

System: ✓ Fault library created: bearing_failures_library

        Severity Levels:

        1. EARLY (Vibration 1.5-2.0 mm/s)
           • Duration: 100 hours to failure
           • Symptoms: Barely noticeable vibration increase
           • Temp increase: +10°F

        2. MILD (Vibration 2.0-3.0 mm/s)
           • Duration: 50 hours to failure
           • Symptoms: Audible noise, slight temp increase
           • Temp increase: +20°F

        3. MODERATE (Vibration 3.0-4.5 mm/s)
           • Duration: 24 hours to failure
           • Symptoms: Noticeable vibration, obvious noise
           • Temp increase: +40°F

        4. SEVERE (Vibration 4.5-7.0 mm/s)
           • Duration: 4 hours to failure
           • Symptoms: Heavy vibration, grinding noise
           • Temp increase: +80°F

        5. CRITICAL (Vibration >7.0 mm/s)
           • Duration: <1 hour to catastrophic failure
           • Symptoms: Extreme vibration, metal-on-metal
           • Temp increase: +150°F

        Library saved. Apply with:
        "Inject bearing failure severity 3 on equipment X"
```

#### Via Configuration File

```yaml
# fault_library.yaml

fault_templates:
  - name: "hydraulic_leak_slow"
    description: "Gradual hydraulic pressure loss over 30 minutes"
    sensors:
      - name: "hydraulic_pressure"
        start_value: 3000
        end_value: 2700
        duration_minutes: 30
        profile: "linear"
        noise: 20  # ±20 PSI random variation

      - name: "hydraulic_oil_temp"
        start_value: 180
        end_value: 195
        duration_minutes: 30
        profile: "exponential"  # Temp rises faster as leak worsens

  - name: "engine_overheating_radiator_clog"
    description: "Overheating due to clogged radiator fins"
    sensors:
      - name: "coolant_temp"
        start_value: 180
        end_value: 240
        duration_minutes: 15
        profile: "exponential"

      - name: "engine_power"
        start_value: 340
        end_value: 280
        duration_minutes: 15
        profile: "linear"  # ECU reduces power to protect engine

      - name: "fan_speed"
        start_value: 50
        end_value: 100
        duration_minutes: 1
        profile: "step"  # Fan immediately goes to 100%

  - name: "fuel_pump_intermittent_failure"
    description: "Fuel pump failing intermittently"
    sensors:
      - name: "fuel_pressure"
        values: [50, 55, 45, 52, 40, 58, 35, 50, 30]  # Intermittent drops
        interval_seconds: 30
        profile: "random_sequence"

      - name: "engine_rpm"
        dependent_on: "fuel_pressure"  # RPM follows fuel pressure
        correlation: 0.8  # 80% correlation
        profile: "correlated"
```

**Load and Apply:**
```bash
curl -X POST http://localhost:8989/api/simulator/load_fault_library \
  -F "file=@fault_library.yaml"

curl -X POST http://localhost:8989/api/simulator/apply_fault_template \
  -d '{
    "equipment_id": "8R_training_005",
    "template_name": "engine_overheating_radiator_clog"
  }'
```

---

## Use Cases for Manual Data Injection

### Use Case 1: Recreating Real Field Failures

**Scenario:** A customer's tractor had a bearing failure last month. You want trainees to practice diagnosing it.

**Steps:**
1. **Export real telemetry** from JDLink (John Deere's real telematics platform)
2. **Anonymize** equipment ID and customer data
3. **Upload to simulator** as training scenario
4. **Replay** for trainees at 10x speed (24 hours → 2.4 hours)

```python
# Script to anonymize and upload real failure data
import pandas as pd

# Load real JDLink export
df = pd.read_csv("jdlink_bearing_failure_20251215.csv")

# Anonymize
df['equipment_id'] = 'ANON_TRAINING_' + df['equipment_id'].apply(hash).astype(str)
df['customer_id'] = 'REDACTED'

# Save anonymized version
df.to_csv("training_bearing_failure_anon.csv", index=False)

# Upload to simulator
sim.upload_csv_replay(
    file_path="training_bearing_failure_anon.csv",
    equipment_id="8R_training_real_failure_001",
    replay_speed=10.0,  # 10x faster than real-time
    loop=False  # Don't loop, play once
)
```

**Training Value:**
- Trainees practice on **real failure patterns** (not just synthetic)
- Learn to recognize **subtle early warning signs**
- See how failures **progress over time**

---

### Use Case 2: Creating Certification Exams

**Scenario:** You need 10 unique exam scenarios, each with precise fault parameters to ensure fair grading.

```python
# Generate 10 exam scenarios with controlled randomness
import random

exam_scenarios = []

for i in range(10):
    # Randomize fault parameters within bounds
    scenario = {
        "exam_id": f"CERT_EXAM_SCENARIO_{i+1:02d}",
        "equipment_id": f"8R_exam_{i+1:02d}",
        "fault_type": random.choice([
            "hydraulic_leak",
            "bearing_wear",
            "fuel_filter_clog",
            "radiator_clog",
            "alternator_failure"
        ]),
        "severity": random.uniform(0.5, 0.9),  # 50-90% severity
        "duration": random.randint(15, 45),  # 15-45 minutes
        "noise_level": random.uniform(0.02, 0.08)  # 2-8% noise
    }

    exam_scenarios.append(scenario)

    # Inject into simulator
    sim.create_fault_scenario(**scenario)

# Save exam key
import json
with open("certification_exam_answer_key.json", "w") as f:
    json.dump(exam_scenarios, f, indent=2)

print("✓ 10 unique exam scenarios created")
print("✓ Answer key saved for grading")
```

**Grading:**
Trainees must correctly identify:
1. Fault type (hydraulic_leak, bearing_wear, etc.)
2. Severity level (within ±10%)
3. Estimated time to failure (within ±20%)

---

### Use Case 3: Edge Case Testing

**Scenario:** Test if ML model can detect **intermittent faults** (hardest to diagnose)

```python
# Create intermittent fuel pump failure pattern
import numpy as np

timestamps = pd.date_range("2026-01-19 15:00", periods=60, freq="1min")

# Fuel pressure: drops randomly, recovers, drops again
fuel_pressure = []
base_pressure = 50  # PSI

for i in range(60):
    if i % 15 == 0 and i > 0:  # Drop every 15 minutes
        drop = np.random.uniform(10, 20)  # Random drop 10-20 PSI
        fuel_pressure.append(base_pressure - drop)
    elif i % 15 in [1, 2, 3]:  # Stay low for 3 minutes
        fuel_pressure.append(fuel_pressure[-1] + np.random.uniform(-2, 2))
    else:  # Recover to normal
        target = base_pressure
        current = fuel_pressure[-1] if fuel_pressure else base_pressure
        recovery = (target - current) * 0.3  # 30% recovery per minute
        fuel_pressure.append(current + recovery + np.random.uniform(-1, 1))

# Inject intermittent pattern
for ts, press in zip(timestamps, fuel_pressure):
    sim.inject_sensor_value(
        equipment_id="8R_edge_case_001",
        sensor="fuel_pressure",
        value=press,
        timestamp=ts.isoformat()
    )

print("✓ Intermittent fault pattern injected")
print("Challenge: Can your ML model detect this pattern?")
```

---

## Best Practices for Manual Injection

### 1. **Always Add Metadata**

```python
# Good: Include metadata for traceability
sim.inject_sensor_value(
    equipment_id="8R_training_001",
    sensor="hydraulic_pressure",
    value=2850,
    timestamp="2026-01-19T15:30:00Z",
    quality="good",
    metadata={
        "injected_by": "instructor_jones",
        "scenario": "hydraulic_leak_cert_exam",
        "expected_diagnosis": "seal_failure",
        "severity": "moderate"
    }
)

# Bad: No context for future reference
sim.inject_sensor_value(
    equipment_id="8R_training_001",
    sensor="hydraulic_pressure",
    value=2850
)
```

### 2. **Use Realistic Sensor Correlations**

```python
# Good: Correlated sensors (realistic)
hydraulic_pressure = 2850  # Decreasing
hydraulic_oil_temp = 195   # Increasing (system straining)
hydraulic_flow = 23        # Decreasing (less fluid available)

# Bad: Uncorrelated (unrealistic)
hydraulic_pressure = 2850  # Decreasing
hydraulic_oil_temp = 180   # Normal (illogical)
hydraulic_flow = 25        # Normal (contradictory)
```

### 3. **Add Sensor Noise**

```python
# Good: Realistic noise
import numpy as np
base_value = 3000
noise = np.random.normal(0, 20, size=100)  # ±20 PSI noise
values = base_value + noise

# Bad: Perfectly smooth (unrealistic)
values = [3000] * 100  # No sensor is this stable
```

### 4. **Document Scenarios**

```python
# Create scenario documentation
scenario_doc = {
    "scenario_id": "CERT_EXAM_001",
    "created_by": "instructor_jones",
    "created_at": "2026-01-19T10:00:00Z",
    "equipment_type": "John Deere 8R-410",
    "fault_type": "hydraulic_leak",
    "learning_objectives": [
        "Detect pressure drop pattern",
        "Calculate leak rate",
        "Estimate time to critical failure"
    ],
    "expected_diagnosis": "Hydraulic seal failure",
    "grading_criteria": {
        "correct_fault_type": 40,  # 40 points
        "accurate_severity": 30,   # 30 points
        "time_to_failure": 30      # 30 points
    }
}

sim.save_scenario_documentation("CERT_EXAM_001", scenario_doc)
```

---

## Conclusion

Manual data injection enables:

1. ✅ **Recreation of real failures** for training on actual patterns
2. ✅ **Precise control** for certification exams and assessments
3. ✅ **Edge case testing** for ML model validation
4. ✅ **Custom scenarios** tailored to specific learning objectives
5. ✅ **Historical replay** of customer incidents for root cause analysis

Combined with automatic generation, this provides **maximum flexibility** for:
- Instructors creating tailored training programs
- Trainees practicing specific diagnostic skills
- Engineers validating ML models
- Managers recreating field incidents for investigation

**The simulator becomes a complete training platform that can handle any scenario—automatic, manual, or hybrid.** 🎯
