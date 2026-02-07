# OT Simulator UI - Implementation Gaps Analysis

**Date:** 2026-02-07
**Spec:** simulator_ui_spec.md
**Current Status:** Partially Implemented

---

## CRITICAL GAPS

### 1. **VENDOR-SPECIFIC OPC UA ENDPOINTS** ❌ NOT IMPLEMENTED

**What Spec Requires (Lines 356-396):**
```
OPC UA SERVER - Active Modes:
┌────────────────────────────────────────────────────────┐
│ Mode           Endpoint                      Nodes     │
├────────────────────────────────────────────────────────┤
│ Generic        :4840 (default)               379       │
│ Kepware        :49320                        379       │  ← KEPWARE CANONICAL PORT!
│ Honeywell      :4897                         1137*     │  ← HONEYWELL CANONICAL PORT!
│                                  *Composite points      │
└────────────────────────────────────────────────────────┘
```

**What's Currently Implemented:**
- ❌ Only ONE OPC UA endpoint: `opc.tcp://localhost:4840`
- ❌ No separate Kepware endpoint on port 49320
- ❌ No separate Honeywell endpoint on port 4897
- ❌ All modes share the same endpoint/port

**Reality:**
- Kepware KEPServerEX uses port 49320 by default
- Honeywell Experion uses port 4897 by default
- **Customers expect these canonical ports** for vendor modes!

**Impact:** 🔴 **HIGH**
- Cannot simulate realistic Kepware/Honeywell integration
- OPC UA clients expecting canonical ports will fail
- Not representative of real vendor environments

---

### 2. **MQTT TOPIC STRUCTURE DISPLAY** ⚠️ PARTIALLY IMPLEMENTED

**What Spec Requires (Lines 399-452):**
```
MQTT PUBLISHER - Active Formats:
┌────────────────────────────────────────────────────────┐
│ Format         Topics Published       Rate    Size     │
├────────────────────────────────────────────────────────┤
│ Generic JSON   sensors/#               2 Hz   379      │
│ Kepware        kepware/#               2 Hz   379      │
│ Sparkplug B    spBv1.0/#              CoV    379      │
│                                    (Change of Value)    │
└────────────────────────────────────────────────────────┘

Topic Trees:
▼ Kepware: kepware/{channel}/{device}/{tag}
  ├─ kepware/Siemens_S7_Crushing/Crusher_01/MotorPower
  ├─ kepware/Siemens_S7_Crushing/Crusher_01/VibrationX
  └─ ... (379 total)

▼ Sparkplug B: spBv1.0/{group}/{type}/{node}/{device}
  ├─ spBv1.0/DatabricksDemo/NBIRTH/OTSimulator01
  ├─ spBv1.0/DatabricksDemo/NDATA/OTSimulator01
  ├─ spBv1.0/DatabricksDemo/DBIRTH/.../MiningAssets
  ├─ spBv1.0/DatabricksDemo/DDATA/.../MiningAssets
  └─ ... (per device)
```

**What's Currently Implemented:**
- ✅ Topic patterns are shown (generic format)
- ⚠️ No actual topic tree expansion
- ❌ No real-time topic list
- ❌ No message rate per format
- ❌ No size statistics per format

**Impact:** 🟡 **MEDIUM**
- Hard to understand actual topic structure
- Cannot easily copy/paste real topics for testing
- No visibility into Sparkplug B lifecycle topics

---

### 3. **SPARKPLUG B SPECIFIC INFO** ⚠️ BASIC ONLY

**What Spec Requires (Lines 159-224):**
```
SPARKPLUG B MODE PANEL:
Configuration:
├─ Group ID: DatabricksDemo
├─ Edge Node ID: OTSimulator01
├─ MQTT Broker: localhost:1883
└─ Protobuf Encoding: ⚪ Disabled (using JSON)

State Management:
┌────────────────────────────────────────────────────────┐
│ Birth/Death Sequence (bdSeq): 3                       │
│ Message Sequence (seq): 1,247                         │
│ Edge Node State: 🟢 OPERATIONAL                       │
│ Last NBIRTH: 2026-02-06 11:23:45 (3h 12m ago)        │
└────────────────────────────────────────────────────────┘

Device Status:
┌────────────────────────────────────────────────────────┐
│ Device ID         State      Last DBIRTH    Metrics   │
├────────────────────────────────────────────────────────┤
│ MiningAssets      🟢 Online   11:23:47      100       │
│ PowerGrid         🟢 Online   11:23:48      80        │
│ ProductionLine    🟢 Online   11:23:49      120       │
│ PipelineMonitor   🟢 Online   11:23:50      79        │
└────────────────────────────────────────────────────────┘
```

**What's Currently Implemented:**
- ✅ Basic pattern shown: `spBv1.0/{group_id}/{message_type}/{edge_node}/{device}`
- ❌ No bdSeq (birth/death sequence) tracking
- ❌ No seq (message sequence) tracking
- ❌ No BIRTH/DATA/DEATH message type breakdown
- ❌ No device-level status
- ❌ No lifecycle event log

**Impact:** 🟡 **MEDIUM**
- Cannot verify Sparkplug B compliance
- Cannot debug sequence number issues
- No visibility into BIRTH certificate contents

---

### 4. **KEPWARE CHANNEL/DEVICE BREAKDOWN** ❌ NOT IMPLEMENTED

**What Spec Requires (Lines 91-155):**
```
KEPWARE MODE PANEL:
Configuration:
├─ OPC UA Endpoint: opc.tcp://localhost:49320  ← SPECIFIC PORT!
├─ MQTT Topic Prefix: kepware/
├─ IoT Gateway Format: ✅ Enabled
└─ Batch by Device: ✅ Enabled

Channel Structure:
┌────────────────────────────────────────────────────────┐
│ Channel              PLC Vendor    Devices    Tags     │
├────────────────────────────────────────────────────────┤
│ Siemens_S7_Crushing  Siemens       8         128      │
│ Modbus_TCP_Fleet     Generic       120       240      │
│ AB_ControlLogix_Util Rockwell      3         11       │
└────────────────────────────────────────────────────────┘

Device Breakdown (Siemens_S7_Crushing):
┌────────────────────────────────────────────────────────┐
│ Device           Equipment Type    Tag Count  Status   │
├────────────────────────────────────────────────────────┤
│ Crusher_01       Primary Crusher   16         🟢 Active│
│ Crusher_02       Secondary Crush   16         🟢 Active│
│ Conveyor_01      Belt Conveyor     16         🟢 Active│
└────────────────────────────────────────────────────────┘
```

**What's Currently Implemented:**
- ✅ Pattern shown: `{channel}.{device}.{tag}`
- ❌ No Channel → PLC mapping table
- ❌ No Device breakdown per channel
- ❌ No tag count per device
- ❌ No equipment type labels
- ❌ No IoT Gateway format indication

**Impact:** 🟡 **MEDIUM**
- Cannot understand Kepware hierarchical structure
- Hard to map sensors to channels/devices
- No visibility into batching behavior

---

### 5. **HONEYWELL EXPERION MODE** ❌ NOT IMPLEMENTED

**What Spec Requires (Lines 228-278):**
```
HONEYWELL EXPERION MODE:
Configuration:
├─ Server Name: MINE_A_EXPERION_PKS
├─ Version: R520
├─ OPC UA Port: 4897  ← CANONICAL PORT!
└─ Composite Points: ✅ Enabled

Point Details (FIM_01 - Sample):
┌────────────────────────────────────────────────────────┐
│ Point                        Attributes       Status   │
├────────────────────────────────────────────────────────┤
│ CRUSH_PRIM_MOTOR_CURRENT     🟢 7 attributes  Active   │
│   ├─ .PV: 850.3 A                                     │
│   ├─ .PVEUHI: 1200.0 A                                │
│   ├─ .PVBAD: false                                    │
│   └─ ... 4 more attributes                            │
└────────────────────────────────────────────────────────┘
```

**What's Currently Implemented:**
- ✅ Pattern shown: `{controller}/{module}/{point}.{attribute}`
- ❌ No composite point structure (.PV, .SP, .OP, etc.)
- ❌ No module organization
- ❌ Mode is described but not actually functional
- ❌ No separate OPC UA server on port 4897

**Impact:** 🟡 **MEDIUM**
- Cannot simulate Honeywell Experion environment
- Missing composite point attributes (required for DCS simulation)
- Not useful for mining/oil&gas customers using Honeywell

---

### 6. **CONNECTED CLIENTS PER ENDPOINT** ❌ NOT IMPLEMENTED

**What Spec Requires (Lines 389-395, 444-450):**
```
Connected Clients (OPC UA):
┌────────────────────────────────────────────────────────┐
│ Client                 Endpoint    Subscriptions       │
├────────────────────────────────────────────────────────┤
│ OPC UA Connector       :4840       25 nodes            │
│ UAExpert (localhost)   :49320      12 nodes (Kepware)  │
└────────────────────────────────────────────────────────┘

Connected Subscribers (MQTT):
┌────────────────────────────────────────────────────────┐
│ Client              Subscribed Topics          QoS     │
├────────────────────────────────────────────────────────┤
│ MQTT Connector      kepware/#                  1       │
│ MQTT Explorer       sensors/mining/#           0       │
└────────────────────────────────────────────────────────┘
```

**What's Currently Implemented:**
- ❌ No client tracking at all
- ❌ No subscription visibility
- ❌ Cannot see who's connected
- ❌ Cannot see what topics/nodes clients are subscribed to

**Impact:** 🟠 **MEDIUM-LOW**
- Cannot debug connection issues
- No visibility into active integrations
- Hard to know if connectors are working

---

### 7. **MESSAGE STATISTICS PER MODE** ⚠️ PARTIALLY IMPLEMENTED

**What Spec Requires (Lines 434-442):**
```
Message Statistics (last hour):
┌────────────────────────────────────────────────────────┐
│ Format         Messages  Avg Size   Total Bytes        │
├────────────────────────────────────────────────────────┤
│ Generic JSON   7,200      245 B     1.7 MB            │
│ Kepware        7,200      312 B     2.2 MB            │
│ Sparkplug B    1,524      1.2 KB    1.8 MB            │
│                (BIRTH/DATA combined)                   │
└────────────────────────────────────────────────────────┘
```

**What's Currently Implemented:**
- ✅ Message counts shown in live inspector
- ❌ No message size tracking
- ❌ No bandwidth statistics
- ❌ No per-mode message rates
- ❌ No historical tracking (just live)

**Impact:** 🟢 **LOW**
- Nice-to-have for performance analysis
- Not critical for basic operation

---

## SUMMARY OF GAPS

### By Priority:

#### 🔴 CRITICAL (Blocks Realistic Simulation):
1. **Vendor-specific OPC UA endpoints** (Kepware:49320, Honeywell:4897)
   - Required for realistic integration testing
   - Customers expect these canonical ports

#### 🟡 MEDIUM (Reduces Usability):
2. **Sparkplug B lifecycle tracking** (bdSeq, seq, BIRTH/DATA/DEATH)
3. **Kepware channel/device breakdown** with tag counts
4. **MQTT topic tree expansion** (actual topic lists, not just patterns)
5. **Honeywell composite points** (.PV, .SP, .OP attributes)

#### 🟠 MEDIUM-LOW (Nice to Have):
6. **Connected clients tracking** (who's subscribed to what)
7. **Message size/bandwidth statistics** per mode

#### 🟢 LOW (Cosmetic):
8. Better visual styling to match spec wireframes

---

## WHAT'S WORKING WELL ✅

1. **Vendor mode patterns are documented** (topic/node patterns shown)
2. **Live message inspector** with protocol/mode/industry filters
3. **Basic connection info** (endpoints, brokers, ports)
4. **Example code snippets** for Python connectivity
5. **PLC vendor information** (channel mappings)

---

## RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: Critical - Vendor Endpoints (Est: 4-6 hours)
1. Create multiple OPC UA server instances on different ports
2. Kepware endpoint on port 49320
3. Honeywell endpoint on port 4897
4. Update connection info UI to show all endpoints
5. Add endpoint selection to OPC UA clients

### Phase 2: Sparkplug B Completeness (Est: 3-4 hours)
1. Track bdSeq and seq numbers
2. Log BIRTH/DATA/DEATH message types
3. Show device-level status
4. Display last BIRTH timestamp per device
5. Add sequence gap detection

### Phase 3: Kepware Channel Breakdown (Est: 2-3 hours)
1. Extract channel → device → tag hierarchy
2. Show device count per channel
3. Show tag count per device
4. Add equipment type labels
5. Display IoT Gateway format status

### Phase 4: MQTT Topic Expansion (Est: 2 hours)
1. List actual MQTT topics being published
2. Show message rate per topic
3. Add expandable topic tree view
4. Show Sparkplug lifecycle topics separately

### Phase 5: Connected Clients (Est: 3-4 hours)
1. Track OPC UA client connections
2. Track MQTT subscribers
3. Show subscribed topics/nodes per client
4. Add client connection/disconnection events

### Phase 6: Honeywell Mode (Est: 6-8 hours)
1. Implement composite point structure
2. Create separate OPC UA server on port 4897
3. Add .PV, .SP, .OP, .PVBAD attributes
4. Organize by modules (FIM, ACE, LCN)
5. Add controller simulation

---

## TESTING VERIFICATION

### How to Verify Implementation:

**Vendor Endpoints:**
```python
# Test Kepware endpoint
from asyncua import Client
client = Client("opc.tcp://localhost:49320")  # Should work!
await client.connect()

# Test Honeywell endpoint
client = Client("opc.tcp://localhost:4897")  # Should work!
await client.connect()
```

**Sparkplug B:**
```bash
# Subscribe and verify BIRTH messages
mosquitto_sub -t 'spBv1.0/+/NBIRTH/#' -v
# Should see: spBv1.0/DatabricksDemo/NBIRTH/OTSimulator01
```

**Kepware Topics:**
```bash
# Verify channel/device/tag structure
mosquitto_sub -t 'kepware/#' -v
# Should see: kepware/Siemens_S7_Crushing/Crusher_01/MotorPower
```

---

## CONCLUSION

**Current State:** 40% of spec implemented
- ✅ Basic connectivity works
- ⚠️ Vendor modes exist but incomplete
- ❌ Canonical ports missing (critical gap)
- ❌ Advanced features not implemented

**To Reach 100%:**
- Implement multiple OPC UA server instances
- Add comprehensive Sparkplug B tracking
- Expand Kepware hierarchical display
- Add client connection tracking
- Complete Honeywell Experion mode

**Estimated Total Effort:** 20-27 hours of focused development
