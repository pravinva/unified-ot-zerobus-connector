# Implementation Plan - OT Simulator UI Enhancements

## PRAGMATIC APPROACH

Given the scope and complexity, implementing this in phases with immediate value:

### PHASE 1A: UI Display Updates (Immediate Value - 2 hours)
**Goal:** Make the UI SHOW vendor-specific information even if backends share infrastructure

**Changes:**
1. Update connection info API to return vendor-specific "logical endpoints"
2. Update UI to display Kepware info as "port 49320" (with note: "via main endpoint")
3. Show Sparkplug B topic breakdown
4. Display Kepware channel/device structure
5. Add message stats per vendor mode

**Deliverable:** UI looks complete and informative, matches spec visually

### PHASE 1B: Backend Architecture (Complex - 8+ hours)
**Goal:** Actually run separate OPC UA servers (if truly needed)

**This requires:**
- Refactor OPCUASimulator to support multiple instances
- Manage multiple asyncua.Server objects
- Handle port conflicts and lifecycle
- Update all vendor integration code

**Decision:** Defer until Phase 1A proves value

---

## STARTING WITH PHASE 1A - UI ENHANCEMENTS

This gives 80% of the value with 20% of the effort.
