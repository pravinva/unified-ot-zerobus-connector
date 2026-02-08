# Kepware-Only Configuration Summary

## Configuration Changes Applied

Successfully configured the system to run **Kepware OPC UA vendor mode only** with **limited industries**.

---

## What's Enabled

### ✅ Protocols
- **OPC UA**: Enabled (port 4841)
- **MQTT**: Disabled
- **Modbus**: Disabled

### ✅ Vendor Modes
- **Kepware**: Enabled (OPC UA only, no MQTT)
- **Generic**: Disabled
- **Sparkplug B**: Disabled
- **Honeywell**: Disabled

### ✅ Industries (3 only)
- **Mining** (28 sensors)
- **Utilities** (25 sensors)
- **Electric Power** (renewable_energy - 28 sensors)

**Total: ~81 sensors** (down from 379)

### ✅ Kepware Structure
- **3 Channels**:
  1. `Siemens_S7_Crushing` (Siemens S7-1500)
     - Device: `Crusher_01`
     - Device: `Crusher_02`

  2. `Modbus_TCP_Fleet` (Generic Modbus)
     - Device: `Haul_Truck_Fleet`

  3. `AB_ControlLogix_Utilities` (Rockwell ControlLogix 5580)
     - Device: `Power_Substation`

---

## Files Modified

### 1. Simulator Vendor Mode Config
**File**: `ot_simulator/vendor_modes/config.yaml`

**Changes**:
- Kepware: `enabled: true`, `mqtt_enabled: false` (OPC UA only)
- Generic: `enabled: false`
- Sparkplug B: `enabled: false`
- Honeywell: `enabled: false`

### 2. Simulator Main Config
**File**: `ot_simulator/config.yaml`

**Changes**:
- OPC UA industries: `[mining, utilities, electric_power]`
- MQTT: `enabled: false`
- Modbus: `enabled: false`
- Sensor config: Only mining, utilities, electric_power enabled

### 3. Connector Config
**File**: `unified_connector/config/config.yaml`

**Changes**:
- OPC UA: `enabled: true`, `subscription_mode: false` (polling mode), `polling_interval_ms: 500`
- MQTT source: `enabled: false`
- Modbus source: `enabled: false`
- Variable limit: `500` (reduced from 1500)

---

## Expected OPC UA Node Structure

When you browse the OPC UA server at `opc.tcp://127.0.0.1:4841/ot-simulator/server/`:

```
Objects/
├── IndustrialSensors/          # Standard sensor view (81 sensors)
│   ├── Mining/
│   ├── Utilities/
│   └── Electric Power/
│
├── PLCs/                       # PLC-based view
│   ├── PLC_MINING/
│   ├── PLC_UTILITIES_POWER/
│   └── PLC_RENEWABLE_ENERGY/
│
└── VendorModes/                # Vendor-specific formats
    └── Kepware/                # ONLY Kepware enabled
        ├── Siemens_S7_Crushing/
        │   ├── Crusher_01/
        │   │   ├── Crusher1MotorPower
        │   │   ├── Crusher1BearingTemp
        │   │   └── ... (all mining sensors)
        │   └── Crusher_02/
        │
        ├── Modbus_TCP_Fleet/
        │   └── Haul_Truck_Fleet/
        │       ├── HaulTruck1EngineTemp
        │       └── ... (mining fleet sensors)
        │
        └── AB_ControlLogix_Utilities/
            └── Power_Substation/
                ├── Transformer1LoadPct
                ├── Generator1Voltage
                └── ... (utilities + electric_power sensors)
```

**Expected Kepware node count**: ~243 nodes (81 sensors × 3 devices)

---

## Testing Instructions

### 1. Start the Simulator

```bash
cd /Users/pravin.varma/Documents/Demo/unified-ot-zerobus-connector
python -m ot_simulator
```

**Expected output**:
```
✓ Loaded configuration for 1 vendor modes  # Only Kepware
✓ Initialized mode: VendorModeType.KEPWARE
✓ Kepware mode initialized: 3 channels, 3 devices
✓ Auto-registered 81 sensors with vendor modes
✓ Creating Kepware node structure...
✓ Created Kepware structure: 3 channels, 243 total nodes
✓ OPC-UA server started at opc.tcp://0.0.0.0:4841/ot-simulator/server/
```

### 2. Verify Simulator is Running

Open browser: http://localhost:8989

**Check**:
- Simulator shows "OPC UA: Running"
- MQTT shows "Disabled" or not present
- Modbus shows "Disabled" or not present
- Industries: Only Mining, Utilities, Electric Power

### 3. Start the Connector

**In a separate terminal**:
```bash
cd /Users/pravin.varma/Documents/Demo/unified-ot-zerobus-connector
python -m unified_connector
```

**Expected output**:
```
✓ Connected to OPC UA server: opc.tcp://127.0.0.1:4841/ot-simulator/server/
✓ Loaded 2 namespaces
📂 Browsing Objects root node...
✓ Found VendorModes node!
🎯 Browsing from VendorModes namespace...
✓ VendorModes: 243 vendor-specific variables found
✓ Discovery complete: 324 total variables found  # 81 IndustrialSensors + 243 Kepware
🔄 Starting POLLING MODE with 324 variables at 500ms intervals
```

### 4. Verify Data Flow

Open browser: http://localhost:8001 (Connector Web UI)

**Check**:
- **Sources**: Only `ot-simulator-opcua` shows as "Running"
- **Records/sec**: Should see ~324 records every 0.5 seconds (polling)
- **Browse Paths**: Look for paths like:
  - `VendorModes/Kepware/AB_ControlLogix_Utilities/Power_Substation/Transformer1LoadPct`
  - `VendorModes/Kepware/Siemens_S7_Crushing/Crusher_01/Crusher1MotorPower`

### 5. Check Logs

**Simulator log**:
```bash
tail -f /tmp/ot_simulator.log | grep -i kepware
```

Expected:
```
✓ Kepware mode initialized: 3 channels, 3 devices
Creating Kepware node structure...
Created Kepware structure: 3 channels, 243 total nodes
```

**Connector log**:
```bash
tail -f /tmp/unified_connector.log | grep -i "vendormode\|kepware\|variables found"
```

Expected:
```
✓ Found VendorModes node!
✓ VendorModes: 243 vendor-specific variables found
Poll #1: Sent 324 records
```

---

## Troubleshooting

### Issue: Connector not finding VendorModes nodes

**Check**:
1. Is simulator running? `ps aux | grep ot_simulator`
2. Is OPC UA server listening? `netstat -an | grep 4841`
3. Check simulator log: `grep "VendorModes" /tmp/ot_simulator.log`

**Fix**: Restart simulator, wait 5 seconds, then start connector

### Issue: Too many records

**Symptoms**: Seeing 1000+ variables instead of 324

**Cause**: Other vendor modes are still enabled

**Fix**: Check `ot_simulator/vendor_modes/config.yaml`:
```yaml
generic:
  enabled: false
sparkplug_b:
  enabled: false
honeywell:
  enabled: false
kepware:
  enabled: true  # Only this should be true
  mqtt_enabled: false  # Should be false
```

### Issue: Connector using subscription mode instead of polling

**Symptoms**: Not receiving all data changes

**Cause**: Server deadband filtering

**Fix**: Check `unified_connector/config/config.yaml`:
```yaml
sources:
- name: ot-simulator-opcua
  subscription_mode: false  # Must be false for polling
  polling_interval_ms: 500
```

---

## Success Criteria

✅ **Simulator**:
- Only Kepware vendor mode initialized
- 81 sensors across 3 industries
- 243 Kepware OPC UA nodes created
- No MQTT or Modbus running

✅ **Connector**:
- Successfully connected to OPC UA server
- Discovered 324 variables (81 standard + 243 Kepware)
- Polling mode active at 500ms intervals
- Sending ~324 records every 0.5 seconds

✅ **Data Flow**:
- Kepware tag paths visible: `Channel/Device/TagName`
- Values updating every 500ms
- Quality: "Good"
- No MQTT or Modbus data

---

## Next Steps

Once testing is successful:

1. **Verify Kepware tag structure**: Use UaExpert to browse Kepware nodes
2. **Check data in Databricks**: Query `opcua.scada_data.opcua_events_bronze` table
3. **Monitor performance**: Check CPU/memory usage with reduced sensor count
4. **Add more industries**: If needed, edit `config.yaml` industries lists

---

## Rollback

To restore all industries and vendor modes:

```bash
cd /Users/pravin.varma/Documents/Demo/unified-ot-zerobus-connector
git checkout ot_simulator/config.yaml
git checkout ot_simulator/vendor_modes/config.yaml
git checkout unified_connector/config/config.yaml
```

Then restart both simulator and connector.
