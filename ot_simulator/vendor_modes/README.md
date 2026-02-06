# Vendor Modes for OT Simulator

This directory contains vendor-specific output format implementations for the OT Simulator, enabling simultaneous multi-vendor industrial data streaming.

## Quick Start

### 1. Enable Modes

Edit `config.yaml`:
```yaml
vendor_modes:
  kepware:
    enabled: true
  sparkplug_b:
    enabled: true
  honeywell:
    enabled: false
```

### 2. Run Tests

```bash
cd /Users/pravin.varma/Documents/Demo/unified-ot-zerobus-connector
PYTHONPATH=. .venv312/bin/python ot_simulator/vendor_modes/test_modes.py
```

### 3. Use in Simulator

```python
from ot_simulator.vendor_modes.integration import VendorModeIntegration

# Initialize
integration = VendorModeIntegration(simulator_manager)
await integration.initialize()

# Format data for all modes
formatted = integration.format_sensor_data(
    "mining/crusher_1_motor_power",
    value=850.3,
    quality=PLCQualityCode.GOOD
)
```

## Supported Vendor Modes

| Mode | Description | Output Format |
|------|-------------|---------------|
| **Generic** | Simple JSON/OPC UA | `Industries/mining/sensor_name` |
| **Kepware** | KEPServerEX Channel.Device.Tag | `Siemens_S7.Crusher_01.MotorPower` |
| **Sparkplug B** | Eclipse IoT standard | `spBv1.0/Group/DDATA/Node/Device` |
| **Honeywell** | Experion PKS composite points | `EXPERION_PKS.FIM_01.POINT.PV` |

## Files

- **`base.py`** - Base classes (VendorMode, ModeConfig, ModeMetrics)
- **`factory.py`** - Mode creation and management
- **`integration.py`** - Integration with simulator
- **`generic.py`** - Generic mode implementation
- **`kepware.py`** - Kepware KEPServerEX mode
- **`sparkplug_b.py`** - Sparkplug B mode
- **`honeywell.py`** - Honeywell Experion mode
- **`config.yaml`** - Configuration file
- **`test_modes.py`** - Test suite

## Example Outputs

### Kepware IoT Gateway Format
```json
{
  "timestamp": 1738851825000,
  "values": [{
    "id": "Siemens_S7_Crushing.Crusher_01.MotorPower",
    "v": 850.3,
    "q": true,
    "t": 1738851825000
  }]
}
```

### Sparkplug B DDATA
```json
{
  "timestamp": 1738851825000,
  "seq": 1247,
  "metrics": [{
    "name": "Crusher/Motor/Power",
    "timestamp": 1738851825000,
    "dataType": "Float",
    "value": 850.3,
    "properties": {"Quality": 192, "EngUnit": "kW"}
  }]
}
```

### Honeywell Composite Point
```json
{
  "server": "MINE_A_EXPERION_PKS",
  "module": "FIM_01",
  "point": "CRUSH_PRIM_MOTOR_CURRENT",
  "attributes": {
    "PV": 850.3,
    "PVEUHI": 1200.0,
    "PVEULO": 0.0,
    "PVUNITS": "A",
    "PVBAD": false,
    "PVHIALM": 1100.0,
    "PVLOALM": 100.0
  }
}
```

## Architecture

```
┌─────────────────────────────────────┐
│  VendorModeIntegration              │
│  - Auto-register sensors            │
│  - Format for all modes             │
│  - Manage mode lifecycle            │
└───────────┬─────────────────────────┘
            │
    ┌───────┴───────┬───────┬────────┐
    │               │       │        │
┌───▼────┐  ┌───────▼──┐ ┌─▼──────┐ ┌▼─────────┐
│Generic │  │ Kepware  │ │Sparkplug│ │Honeywell │
│Mode    │  │ Mode     │ │B Mode   │ │Mode      │
└────────┘  └──────────┘ └─────────┘ └──────────┘
```

## Configuration

### Channel Mappings (Kepware)
```yaml
kepware:
  settings:
    channel_mappings:
      channels:
        - name: "Siemens_S7_Crushing"
          driver_type: "Siemens TCP/IP Ethernet"
          plc_vendor: "siemens"
          devices:
            - name: "Crusher_01"
              sensors: []  # Auto-populated
```

### Device Mappings (Sparkplug B)
```yaml
sparkplug_b:
  settings:
    group_id: "DatabricksDemo"
    edge_node_id: "OTSimulator01"
    cov_threshold: 0.01  # 1% change threshold
    device_mappings:
      MiningAssets:
        industries: ["mining"]
```

### Module Configuration (Honeywell)
```yaml
honeywell:
  settings:
    server_name: "MINE_A_EXPERION_PKS"
    pks_version: "R520"
    modules:
      FIM_01:
        type: "FIM"  # Field I/O Module
      ACE_01:
        type: "ACE"  # Advanced Control (PID controllers)
```

## API

### Get Mode Status
```python
# Single mode
status = integration.get_mode_status(VendorModeType.KEPWARE)

# All modes
all_status = integration.get_all_mode_status()
```

### Get Diagnostics
```python
# Kepware: channels, devices, tags, quality distribution
diag = integration.get_mode_diagnostics(VendorModeType.KEPWARE)

# Sparkplug B: edge node, devices, sequences, birth/death tracking
diag = integration.get_mode_diagnostics(VendorModeType.SPARKPLUG_B)

# Honeywell: modules, points, controllers, node count
diag = integration.get_mode_diagnostics(VendorModeType.HONEYWELL)
```

### Get Paths
```python
# OPC UA node ID
node_id = integration.get_opcua_node_id(
    "mining/crusher_1_motor_power",
    mode_type=VendorModeType.KEPWARE
)
# Returns: "ns=2;s=Siemens_S7_Crushing.Crusher_01.MotorPower"

# MQTT topic
topic = integration.get_mqtt_topic(
    "mining/crusher_1_motor_power",
    mode_type=VendorModeType.SPARKPLUG_B
)
# Returns: "spBv1.0/DatabricksDemo/DDATA/OTSimulator01/MiningAssets"
```

### Enable/Disable Modes
```python
# Enable mode dynamically
await integration.enable_mode(VendorModeType.HONEYWELL)

# Disable mode
await integration.disable_mode(VendorModeType.HONEYWELL)
```

## Performance

**Message Rates:**
- Generic: 379 msg/sec
- Kepware: 379 msg/sec (can batch by device)
- Sparkplug B: 150-200 msg/sec (Change of Value only)
- **Total: ~900-1000 msg/sec**

**Bandwidth:** ~2.3 Mbps (negligible for modern networks)

**Memory:** <20 MB total for all modes

## Testing

Run the test suite:
```bash
PYTHONPATH=. .venv312/bin/python ot_simulator/vendor_modes/test_modes.py
```

Expected output:
```
============================================================
TESTING KEPWARE MODE
============================================================
✓ Kepware mode initialized
✓ Registered sensor with Kepware mode
OPC UA Node ID: ns=2;s=Siemens_S7_Crushing.Crusher_01.MotorPower
MQTT Topic: kepware/Siemens_S7_Crushing/Crusher_01/MotorPower
✓ Kepware mode test completed

============================================================
TESTING SPARKPLUG B MODE
============================================================
✓ Sparkplug B mode initialized
✓ Registered sensor with Sparkplug B mode
NBIRTH: {'timestamp': ..., 'seq': 0, 'metrics': [...]}
DBIRTH: {'timestamp': ..., 'seq': 1, 'metrics': [...]}
MQTT Topic: spBv1.0/DatabricksDemo/DDATA/OTSimulator01/MiningAssets
✓ Sparkplug B mode test completed

============================================================
TESTING HONEYWELL EXPERION MODE
============================================================
✓ Honeywell Experion mode initialized
✓ Registered sensor with Honeywell mode
OPC UA Node ID: ns=2;s=EXPERION_PKS.FIM_01.CRUSHER_1_MOTOR_POWER.PV
✓ Honeywell Experion mode test completed

============================================================
ALL TESTS PASSED ✓
============================================================
```

## Documentation

See parent directory:
- **`VENDOR_MODES_IMPLEMENTATION.md`** - Comprehensive implementation guide (500+ lines)
- **`VENDOR_MODES_STATUS.md`** - Current status and next steps

## Next Steps

1. **Integration** - Connect to opcua_simulator.py and mqtt_simulator.py
2. **Web UI** - Add Modes tab to professional_web_ui.py
3. **API Endpoints** - Add mode management to web_server.py
4. **Testing** - End-to-end testing with real clients

## Support

For questions or issues, refer to the main documentation or contact the development team.
