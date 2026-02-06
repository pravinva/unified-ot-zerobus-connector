# Fix Git repository permissions:
sudo chown -R pravin.varma:staff .git

# Fix vendor modes directory:
sudo chown -R pravin.varma:staff ot_simulator/vendor_modes/

# Fix other directories with permission issues:
sudo chown -R pravin.varma:staff .zap/
sudo chown -R pravin.varma:staff config/siem/
sudo chown -R pravin.varma:staff scripts/
sudo chown -R pravin.varma:staff tests/security/
sudo chown -R pravin.varma:staff examples/
sudo chown -R pravin.varma:staff ot_simulator/streaming/

# After running these commands, you can commit:
git add ot_simulator/vendor_modes/ VENDOR_MODES_IMPLEMENTATION.md VENDOR_MODES_STATUS.md
git commit -m "feat: Add vendor mode support (Kepware, Sparkplug B, Honeywell)

Implements vendor-specific output formats for OT Simulator:
- Kepware KEPServerEX mode (Channel.Device.Tag structure)
- Sparkplug B mode (BIRTH/DATA/DEATH lifecycle)  
- Honeywell Experion mode (composite points)
- Generic mode (simple JSON/OPC UA)

Features:
- Multi-mode simultaneous operation
- Auto-registration of 379 sensors
- PLC integration (quality codes, scan cycles)
- Metrics and diagnostics per mode
- YAML configuration system

Documentation: VENDOR_MODES_IMPLEMENTATION.md, VENDOR_MODES_STATUS.md

Next: Web UI integration, API endpoints, testing
"
