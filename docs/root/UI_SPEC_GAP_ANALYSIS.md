# UI Specification Gap Analysis
**Date:** 2026-02-07
**Spec File:** simulator_ui_spec.md (1498 lines)
**Current Implementation:** ot_simulator/web_ui/templates.py

---

## EXECUTIVE SUMMARY

**Spec Completion: ~25% of full specification**

The current UI has basic vendor mode panels but is missing most of the comprehensive features outlined in the spec. The spec is extremely detailed and production-grade, while current implementation has only foundational elements.

---

## CRITICAL MISSING SECTIONS

### 1. ❌ Dashboard Tab Enhancements (Lines 26-61)
**Spec Requirements:**
- Overview status cards with uptime
- Active protocols section showing client counts
- Vendor output modes summary cards

**Current Status:** MISSING
- No dashboard overview showing mode status
- No vendor mode cards on dashboard
- No client connection tracking

---

### 2. ⚠️ Modes Tab - Mode Selection & Status (Lines 65-85)
**Spec Requirements:**
```
☑ Generic Mode          (Simple JSON/OPC UA - default)
☑ Kepware Mode          (Channel.Device.Tag structure)
☑ Sparkplug B Mode      (Industry standard MQTT)
☐ Honeywell Experion    (Composite points .PV/.SP/.OP)
```

**Current Status:** PARTIAL
- ✅ Mode cards exist
- ❌ No checkboxes for enable/disable
- ❌ No "Apply Changes" / "Restart Simulators" buttons
- ❌ Mode selection is not interactive

---

### 3. ⚠️ Kepware Mode Panel (Lines 91-155)
**Spec Requirements:**
- Configuration display (OPC UA endpoint, MQTT prefix, IoT Gateway format)
- Channel structure table
- Device breakdown with equipment types
- Sample tags with current values
- Full paths for testing
- MQTT message preview
- Action buttons

**Current Status:** PARTIAL
- ✅ Channel structure with device breakdown (Phase 3)
- ✅ Equipment types displayed
- ❌ Sample tags section missing
- ❌ Current values not shown
- ❌ Full paths display missing
- ❌ MQTT message preview missing
- ❌ Action buttons missing

---

### 4. ⚠️ Sparkplug B Mode Panel (Lines 159-224)
**Spec Requirements:**
- Configuration section
- State management (bdSeq, seq, edge node state, last NBIRTH)
- Device status table
- Recent messages table
- Topic preview (latest DDATA)
- Lifecycle action buttons

**Current Status:** PARTIAL
- ✅ Configuration displayed (Phase 2)
- ✅ State management section (Phase 2)
- ✅ Device status table (Phase 2)
- ❌ Recent messages table missing
- ❌ Topic preview missing
- ❌ Lifecycle action buttons missing (Force Rebirth, Simulate Disconnect, View Birth Certificate)

---

### 5. ❌ Honeywell Experion Mode Panel (Lines 228-278)
**Spec Requirements:**
- Configuration (server name, version, port, composite points)
- Module organization table
- Point details with attributes (.PV, .PVEUHI, .PVBAD, etc.)
- Controller status table
- OPC UA node paths
- Action buttons

**Current Status:** MISSING
- Mode described but not functional
- No UI panel for Honeywell mode

---

### 6. ❌ PLCs Tab Enhancement (Lines 282-348)
**Spec Requirements:**
- PLC dashboard with mode integration
- Vendor mode mappings per PLC
- Show which PLC feeds which Kepware channel/Sparkplug device
- Quality distribution bars

**Current Status:** MISSING
- No mode integration in PLCs tab
- No vendor mode mappings displayed

---

### 7. ⚠️ Protocols Tab Enhancement (Lines 352-452)
**Spec Requirements:**

**OPC UA Section:**
- Active Modes table showing multiple endpoints
- Node structure preview with expandable trees
- Connected clients table

**Current Status:** PARTIAL
- ✅ Vendor endpoints shown (Phase 1A)
- ❌ Node structure preview missing
- ❌ Connected clients tracking missing

**MQTT Section:**
- Active formats table (Generic JSON, Kepware, Sparkplug B)
- Topic trees (expandable)
- Message statistics table
- Connected subscribers table

**Current Status:** PARTIAL
- ✅ Topic tracking API exists (Phase 4)
- ❌ Topic tree UI display missing
- ❌ Message statistics table missing
- ❌ Connected subscribers missing

---

### 8. ❌ Mode Comparison Matrix (Lines 458-488)
**Spec Requirements:**
- Feature comparison table across modes
- Real-time message rate chart (last 60 seconds)
- Legend with color coding

**Current Status:** MISSING
- No comparison matrix
- No real-time charts

---

### 9. ❌ Kepware Diagnostics Panel (Lines 496-538)
**Spec Requirements:**
- Channel health table
- Device health table with last message times
- Quality distribution bar chart
- IoT Gateway format compliance checks
- Action buttons

**Current Status:** MISSING
- Basic diagnostics exist but not in detailed panel format

---

### 10. ⚠️ Sparkplug B Diagnostics Panel (Lines 542-605)
**Spec Requirements:**
- Edge node status
- Device states table
- Message type distribution table
- Sequence number tracking (no gaps, out of order, duplicates)
- Specification compliance checklist
- Lifecycle events log table
- Action buttons

**Current Status:** PARTIAL
- ✅ Edge node status (Phase 2)
- ✅ Device states (Phase 2)
- ❌ Message type distribution table missing
- ❌ Sequence tracking visualization missing
- ❌ Compliance checklist missing
- ❌ Lifecycle events log missing
- ❌ Action buttons missing

---

### 11. ❌ Mode Configuration Interface (Lines 663-730)
**Spec Requirements:**
- Interactive mode setup wizard
- Step 1: Map PLCs to Channels
- Step 2: Define Device Grouping
- Step 3: Tag Naming Convention
- Step 4: Protocol Settings
- Save/Test/Apply buttons

**Current Status:** MISSING
- No interactive configuration UI
- Configuration only via YAML files

---

### 12. ❌ Live Monitoring Dashboard (Lines 734-777)
**Spec Requirements:**
- Message flow diagram (Source → Destination with rates)
- Network throughput charts
- Error tracking table

**Current Status:** MISSING
- No live monitoring dashboard

---

### 13. ⚠️ Live Message Inspector (Lines 1258-1298)
**Spec Requirements:**
- Mode and protocol filters
- Auto-scrolling message display
- Expandable message panels with JSON
- Copy/Validate/Export buttons
- Pause/Resume functionality

**Current Status:** PARTIAL
- ✅ Exists with protocol/mode/industry filters
- ✅ Message display with JSON
- ❌ Expandable panels missing
- ❌ Action buttons missing
- ❌ Pause/Resume missing

---

### 14. ❌ Mode Testing Interface (Lines 1072-1125)
**Spec Requirements:**
- Connection tests per mode
- Format validation
- Sample message testing
- Connector integration tests
- Export tools

**Current Status:** MISSING
- No testing interface

---

### 15. ❌ Real-Time Monitoring Widgets (Lines 1129-1179)
**Spec Requirements:**
- Kepware widget (channels, devices, tags, rate, quality)
- Sparkplug B widget (edge node, devices, seq, bdSeq, rate)
- Honeywell widget (modules, points, controllers)

**Current Status:** MISSING
- No dashboard widgets

---

### 16. ❌ Log Viewer (Lines 1183-1210)
**Spec Requirements:**
- Mode-filtered event logs
- Level filters
- Time range filters
- Export/Clear/Search functionality

**Current Status:** MISSING
- No mode-specific log viewer

---

### 17. ❌ Settings Tab Enhancement (Lines 1214-1254)
**Spec Requirements:**
- Global mode settings
- Configuration file manager
- Mode templates library

**Current Status:** MISSING
- No mode settings in UI

---

## WHAT'S IMPLEMENTED (25%)

### ✅ Completed Features:

1. **Basic Mode Cards** (Modes tab)
   - Generic, Kepware, Sparkplug B, Honeywell cards
   - Enable/disable status display
   - Basic stats (devices, tags, etc.)

2. **Kepware Channel/Device Hierarchy** (Phase 3)
   - Channel table with PLC info
   - Device breakdown with equipment types
   - Tag counts per device

3. **Sparkplug B Lifecycle Tracking** (Phase 2)
   - Configuration display
   - State management (bdSeq, seq, edge node state)
   - Device status table
   - Last NBIRTH timestamp

4. **Connection Info Tab** (Phase 1A)
   - Vendor-specific OPC UA endpoints
   - Canonical ports (Kepware:49320, Honeywell:4897)
   - MQTT broker info

5. **Live Message Inspector** (Partial)
   - Protocol filter (MQTT/OPC-UA/Modbus)
   - Mode filter (Generic/Kepware/Sparkplug B/Honeywell)
   - Industry filter
   - Message type badges for Sparkplug B
   - Real-time message display

6. **MQTT Topics API** (Phase 4)
   - `/api/modes/topics/active` endpoint
   - Topic tracking with message rates
   - But NO UI display

---

## MISSING UI ELEMENTS BY CATEGORY

### 📊 Visualization & Charts (HIGH PRIORITY)
- Real-time message rate charts (last 60 seconds)
- Quality distribution bar charts
- Network throughput graphs
- Sequence tracking visualizations
- Mode comparison charts

### 📝 Data Tables (HIGH PRIORITY)
- Recent messages table (Sparkplug B)
- Message type distribution table
- Lifecycle events log
- Connected clients table (OPC UA & MQTT)
- Channel health table
- Device health table
- Error tracking table

### 🎛️ Interactive Controls (MEDIUM PRIORITY)
- Mode enable/disable checkboxes
- Apply Changes / Restart buttons
- Force Rebirth / Simulate Disconnect buttons
- View Birth Certificate button
- Pause/Resume message inspector
- Configuration editor

### 📋 Detail Displays (MEDIUM PRIORITY)
- Sample tags with current values
- Full OPC UA/MQTT paths
- MQTT message preview
- Topic preview (latest DDATA)
- Node structure preview (expandable tree)
- Compliance checklist

### 🔧 Testing & Debugging Tools (LOW PRIORITY)
- Connection test interface
- Format validator
- Sample message tester
- Export tools (CSV, JSON, YAML)
- Log viewer

### 📱 Dashboard Widgets (LOW PRIORITY)
- Kepware widget
- Sparkplug B widget
- Honeywell widget
- Message flow diagram

---

## PRIORITY RECOMMENDATIONS

### 🔴 PHASE 5 - HIGH IMPACT (Next Implementation)
**Goal:** Add critical missing visualizations and tables

1. **Recent Messages Table** (Sparkplug B panel)
   - Time, Type, Topic, Seq columns
   - Last 10 messages

2. **Sample Tags Display** (Kepware panel)
   - Show 5-10 sample tags with current values
   - Tag name, current value, quality, last updated

3. **Quality Distribution Bars** (Kepware & Sparkplug B)
   - Visual bar chart showing Good/Bad/Uncertain percentages

4. **Message Type Distribution** (Sparkplug B)
   - Table showing NBIRTH, DBIRTH, NDATA, DDATA counts

5. **Connected Clients Tables** (Protocols tab)
   - OPC UA clients with endpoints and subscriptions
   - MQTT subscribers with topics and QoS

**Estimated Effort:** 4-6 hours

---

### 🟡 PHASE 6 - INTERACTIVE CONTROLS
**Goal:** Make UI more interactive

1. **Mode Enable/Disable Toggles**
   - Working checkboxes with API calls
   - Apply Changes button

2. **Action Buttons** (Sparkplug B)
   - Force Rebirth
   - Simulate Disconnect
   - View Birth Certificate

3. **Message Inspector Controls**
   - Pause/Resume
   - Copy message
   - Export last 100

4. **Expandable Panels**
   - Click to expand message details
   - Click to expand channel devices

**Estimated Effort:** 3-4 hours

---

### 🟢 PHASE 7 - ADVANCED FEATURES
**Goal:** Production-grade polish

1. **Topic Tree UI Display** (MQTT)
   - Hierarchical tree view
   - Message rates per topic
   - Sparkplug lifecycle topics grouped

2. **Real-Time Charts**
   - Message rate over last 60 seconds
   - Network throughput by protocol

3. **Configuration Editor**
   - Interactive mode setup wizard
   - PLC to channel mapping

4. **Testing Interface**
   - Connection tests
   - Format validation
   - Export tools

**Estimated Effort:** 8-10 hours

---

## SPEC ACCURACY ASSESSMENT

The specification is **extremely comprehensive** and production-grade. It covers:
- ✅ Complete dashboard redesign
- ✅ All vendor mode panels in detail
- ✅ Diagnostics for each mode
- ✅ Testing and debugging tools
- ✅ Interactive configuration
- ✅ Real-time monitoring
- ✅ API endpoints
- ✅ Visual design guidelines

**The spec is realistic and well-thought-out** for a professional OT simulator product.

---

## SUMMARY

**Current Implementation: 25% of full spec**

**Strengths:**
- Core mode panels exist
- Sparkplug B lifecycle tracking is solid
- Kepware hierarchy is complete
- Message inspector works

**Major Gaps:**
- No dashboard integration
- Missing most data tables
- No charts/visualizations
- No interactive configuration
- No testing tools
- Limited action buttons

**Recommendation:** Implement Phase 5 (HIGH IMPACT) features next to reach 40-50% of spec coverage. These features provide immediate value with moderate effort.
