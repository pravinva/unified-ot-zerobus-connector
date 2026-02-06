"""OPC-UA Server Simulator with realistic industrial data.

Runs a fully functional OPC-UA server that can be connected to by any OPC-UA client.
Uses asyncua library to create server with proper node structure.

Security Features (OPC UA 10101 compliant):
- Basic256Sha256 encryption
- Certificate-based authentication
- Username/password authentication
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from asyncua import Server, ua
from asyncua.common.node import Node

from ot_simulator.sensor_models import IndustryType, SensorSimulator, get_industry_sensors
from ot_simulator.opcua_security import (
    OPCUASecurityConfig,
    OPCUASecurityManager,
    create_security_config_from_dict,
)

# Import vendor mode integration
try:
    from ot_simulator.vendor_modes.integration import VendorModeIntegration
    from ot_simulator.vendor_modes.base import VendorModeType
    VENDOR_MODES_AVAILABLE = True
except ImportError:
    VendorModeIntegration = None  # type: ignore
    VendorModeType = None  # type: ignore
    VENDOR_MODES_AVAILABLE = False

logger = logging.getLogger("ot_simulator.opcua")


class OPCUASimulator:
    """OPC-UA Server simulator with realistic sensor data."""

    def __init__(
        self,
        config,
        simulator_manager=None,
    ):
        # Support both config object and legacy direct parameters
        if hasattr(config, "endpoint"):
            self.endpoint = config.endpoint
            self.name = config.server_name
            self.industries = config.industries or list(IndustryType)
            # Extract security configuration
            security_config_dict = getattr(config, "security", {})
            self.security_config = create_security_config_from_dict(security_config_dict)
        else:
            # Legacy support: config is actually endpoint string
            self.endpoint = config
            self.name = "OT Data Simulator"
            self.industries = list(IndustryType)
            self.security_config = OPCUASecurityConfig()  # Default: no security

        self.server: Server | None = None
        self.simulators: dict[str, SensorSimulator] = {}
        self.nodes: dict[str, Node] = {}
        self._running = False
        self._server_task = None
        self._initialized = False  # Track if init() completed successfully
        self.simulator_manager = simulator_manager  # Reference to SimulatorManager for PLC access
        self.vendor_integration: VendorModeIntegration | None = None

        # Initialize security manager
        self.security_manager = OPCUASecurityManager(self.security_config)

    async def init(self):
        """Initialize OPC-UA server with PLC-based hierarchical structure."""
        try:
            logger.info("Creating OPC-UA Server instance...")

            # Validate security configuration
            if not self.security_manager.validate_configuration():
                raise ValueError("Invalid security configuration")

            self.server = Server()
            await self.server.init()
            logger.info("OPC-UA Server instance created")

            self.server.set_endpoint(self.endpoint)
            self.server.set_server_name(self.name)

            # Configure security
            security_policies = self.security_manager.get_security_policies()
            self.server.set_security_policy(security_policies)

            # Set certificate and private key if security is enabled
            if self.security_config.enabled:
                cert_path = self.security_manager.get_certificate_path()
                key_path = self.security_manager.get_private_key_path()

                if cert_path and key_path:
                    await self.server.load_certificate(cert_path)
                    await self.server.load_private_key(key_path)
                    logger.info("✓ Loaded server certificate and private key")

            # Set user manager if username/password auth is enabled
            if self.security_config.enable_user_auth and self.security_manager.user_manager:
                self.server.set_user_manager(self.security_manager.user_manager)
                logger.info(f"✓ Enabled username/password authentication ({len(self.security_config.users)} users)")
            else:
                logger.info("Username/password authentication disabled (anonymous access allowed)")

            # Setup namespace
            uri = "http://databricks.com/iot-simulator"
            idx = await self.server.register_namespace(uri)
            logger.info(f"Registered namespace with index {idx}")

            # Check if PLC simulation is enabled
            has_plc_manager = (
                self.simulator_manager
                and hasattr(self.simulator_manager, 'plc_manager')
                and self.simulator_manager.plc_manager
                and self.simulator_manager.plc_manager.enabled
            )

            # Initialize vendor mode integration if available
            if VENDOR_MODES_AVAILABLE and self.simulator_manager:
                try:
                    self.vendor_integration = VendorModeIntegration(self.simulator_manager)
                    await self.vendor_integration.initialize()
                    logger.info("✓ Vendor mode integration initialized for OPC UA")
                except Exception as e:
                    logger.warning(f"Failed to initialize vendor modes: {e}")
                    self.vendor_integration = None

            # Create BOTH structures for maximum flexibility
            logger.info("Creating dual node structure (PLCs + Industries)")
            await self._create_direct_sensor_nodes(idx)  # IndustrialSensors view

            if has_plc_manager:
                logger.info("Adding PLC-based node structure")
                await self._create_plc_based_nodes(idx)  # PLCs view
            else:
                logger.info("PLC Manager not available - only IndustrialSensors view created")

            # Create vendor-specific node structures if enabled
            if self.vendor_integration:
                logger.info("Creating vendor-specific node structures")
                await self._create_vendor_mode_nodes(idx)

            self._initialized = True
            logger.info(
                f"✓ Initialized OPC-UA server with {len(self.simulators)} sensors"
            )
        except Exception as e:
            logger.exception(f"FATAL ERROR during OPC-UA server initialization: {e}")
            raise

    async def _create_plc_based_nodes(self, idx: int):
        """Create PLC-based hierarchical OPC-UA node structure.

        Structure:
        Objects/
          PLCs/
            PLC_MINING (Rockwell ControlLogix 5580)/
              Diagnostics/
                ScanCount, Mode, Errors, etc.
              Inputs/
                mining/
                  crusher_1_motor_power
                  crusher_1_vibration
              ForcedValues/
        """
        root = await self.server.nodes.objects.add_object(idx, "PLCs")
        logger.info("Creating PLC-based node structure...")

        plc_manager = self.simulator_manager.plc_manager
        all_plcs = plc_manager.get_all_plcs()

        for plc_name, plc_info in all_plcs.items():
            vendor = plc_info['vendor']
            model = plc_info['model']
            industries = plc_info['industries']

            logger.info(f"Creating PLC node: {plc_name} ({vendor} {model})")
            plc_label = f"{plc_name} ({vendor.title()} {model})"
            plc_node = await root.add_object(idx, plc_label)

            # Create Diagnostics folder
            diag_node = await plc_node.add_object(idx, "Diagnostics")

            # Add diagnostic properties
            await diag_node.add_variable(idx, "Vendor", vendor, varianttype=ua.VariantType.String)
            await diag_node.add_variable(idx, "Model", model, varianttype=ua.VariantType.String)
            await diag_node.add_variable(idx, "RunMode", plc_info['run_mode'], varianttype=ua.VariantType.String)
            await diag_node.add_variable(idx, "ScanCycleMs", plc_info['scan_cycle_ms'], varianttype=ua.VariantType.Int32)
            await diag_node.add_variable(idx, "Rack", plc_info['rack'], varianttype=ua.VariantType.Int32)
            await diag_node.add_variable(idx, "Slot", plc_info['slot'], varianttype=ua.VariantType.Int32)

            # Diagnostic counters (will be updated in real-time)
            scan_count_node = await diag_node.add_variable(idx, "TotalScans", 0, varianttype=ua.VariantType.Int64)
            await scan_count_node.set_writable()
            self.nodes[f"_diag_{plc_name}_scan_count"] = scan_count_node

            # Create Inputs folder (realistic PLC terminology)
            inputs_node = await plc_node.add_object(idx, "Inputs")

            # Add sensors for each industry this PLC controls
            for industry in industries:
                industry_enum = IndustryType(industry)
                sensors = get_industry_sensors(industry_enum)

                if not sensors:
                    continue

                industry_node = await inputs_node.add_object(idx, industry.replace('_', ' ').title())
                logger.info(f"  Adding {len(sensors)} inputs for {industry}")

                for simulator in sensors:
                    config = simulator.config
                    sensor_path = f"{industry}/{config.name}"

                    # Create sensor node with PLC metadata
                    sensor_node = await industry_node.add_variable(
                        idx,
                        config.name,
                        simulator.get_value(),
                        varianttype=ua.VariantType.Double,
                    )

                    # Make writable for fault injection
                    await sensor_node.set_writable()

                    # Add OPC-UA properties (metadata)
                    await sensor_node.add_property(idx, "Unit", config.unit, varianttype=ua.VariantType.String)
                    await sensor_node.add_property(
                        idx, "SensorType", config.sensor_type.value, varianttype=ua.VariantType.String
                    )
                    await sensor_node.add_property(idx, "MinValue", config.min_value, varianttype=ua.VariantType.Double)
                    await sensor_node.add_property(idx, "MaxValue", config.max_value, varianttype=ua.VariantType.Double)

                    # PLC-specific properties
                    await sensor_node.add_property(idx, "PLCName", plc_name, varianttype=ua.VariantType.String)
                    await sensor_node.add_property(idx, "PLCModel", model, varianttype=ua.VariantType.String)

                    # Store for updates
                    self.simulators[sensor_path] = simulator
                    self.nodes[sensor_path] = sensor_node

            # Create ForcedValues folder
            forced_node = await plc_node.add_object(idx, "ForcedValues")
            forced_count_node = await forced_node.add_variable(idx, "Count", 0, varianttype=ua.VariantType.Int32)
            await forced_count_node.set_writable()
            self.nodes[f"_diag_{plc_name}_forced_count"] = forced_count_node

    async def _create_direct_sensor_nodes(self, idx: int):
        """Create direct sensor node structure (no PLC layer).

        Structure:
        Objects/
          IndustrialSensors/
            Mining/
              crusher_1_motor_power
              crusher_1_vibration
        """
        root = await self.server.nodes.objects.add_object(idx, "IndustrialSensors")
        logger.info("Creating direct sensor node structure...")

        for i, industry in enumerate(self.industries):
            # Handle both IndustryType enum and string from config
            industry_name = industry.value if hasattr(industry, 'value') else industry
            industry_enum = industry if hasattr(industry, 'value') else IndustryType(industry)

            logger.info(f"Creating industry folder {i+1}/{len(self.industries)}: {industry_name}")
            industry_node = await root.add_object(idx, industry_name.replace('_', ' ').title())

            sensors = get_industry_sensors(industry_enum)
            logger.info(f"  Adding {len(sensors)} sensors for {industry_name}...")

            for j, simulator in enumerate(sensors):
                config = simulator.config
                node_name = config.name

                # Create sensor node
                sensor_node = await industry_node.add_variable(
                    idx,
                    node_name,
                    simulator.get_value(),
                    varianttype=ua.VariantType.Double,
                )

                # Make it writable (for testing fault injection)
                await sensor_node.set_writable()

                # Add metadata as properties
                await sensor_node.add_property(idx, "Unit", config.unit, varianttype=ua.VariantType.String)
                await sensor_node.add_property(
                    idx, "SensorType", config.sensor_type.value, varianttype=ua.VariantType.String
                )
                await sensor_node.add_property(idx, "MinValue", config.min_value, varianttype=ua.VariantType.Double)
                await sensor_node.add_property(idx, "MaxValue", config.max_value, varianttype=ua.VariantType.Double)
                await sensor_node.add_property(
                    idx, "NominalValue", config.nominal_value, varianttype=ua.VariantType.Double
                )

                # Store for updates
                full_path = f"{industry_name}/{node_name}"
                self.simulators[full_path] = simulator
                self.nodes[full_path] = sensor_node

                if (j + 1) % 10 == 0:
                    logger.info(f"    Created {j+1}/{len(sensors)} sensors for {industry_name}")

    async def _create_vendor_mode_nodes(self, idx: int):
        """Create vendor-specific OPC UA node structures.

        Creates separate node hierarchies for each enabled vendor mode:
        - Kepware: Channel.Device.Tag structure
        - Sparkplug B: Group/Edge Node/Device structure (mostly MQTT, but OPC UA nodes for reference)
        - Honeywell: Server.Module.Point structure with composite attributes
        - Generic: Simple flat structure
        """
        if not self.vendor_integration:
            return

        root = await self.server.nodes.objects.add_object(idx, "VendorModes")
        logger.info("Creating vendor-specific node structures...")

        active_modes = self.vendor_integration.mode_manager.get_active_modes()

        for mode in active_modes:
            mode_type = mode.config.mode_type
            mode_name = mode_type.value.replace('_', ' ').title()

            # Create mode root folder
            mode_root = await root.add_object(idx, mode_name)
            logger.info(f"  Creating {mode_name} node structure...")

            # Register all sensors with the mode first
            for sensor_path, simulator in self.simulators.items():
                # Get PLC if available using the correct method
                plc = None
                if self.simulator_manager and hasattr(self.simulator_manager, 'plc_manager'):
                    plc_mgr = self.simulator_manager.plc_manager
                    if plc_mgr and hasattr(plc_mgr, 'get_plc_for_sensor'):
                        plc = plc_mgr.get_plc_for_sensor(sensor_path)

                mode.register_sensor(sensor_path, plc_instance=plc)

            # Create vendor-specific node structure
            if mode_type == VendorModeType.KEPWARE:
                await self._create_kepware_nodes(idx, mode_root, mode)
            elif mode_type == VendorModeType.SPARKPLUG_B:
                await self._create_sparkplug_nodes(idx, mode_root, mode)
            elif mode_type == VendorModeType.HONEYWELL:
                await self._create_honeywell_nodes(idx, mode_root, mode)
            elif mode_type == VendorModeType.GENERIC:
                await self._create_generic_nodes(idx, mode_root, mode)

        logger.info(f"✓ Created vendor-specific nodes for {len(active_modes)} modes")

    async def _create_kepware_nodes(self, idx: int, parent: Node, mode):
        """Create Kepware Channel.Device.Tag structure."""
        # Get channels from mode
        channels = getattr(mode, 'channels', {})

        for channel_name, channel_info in channels.items():
            channel_node = await parent.add_object(idx, channel_name)

            # Get devices in this channel
            devices = channel_info.get('devices', {})
            for device_name, device_info in devices.items():
                device_node = await channel_node.add_object(idx, device_name)

                # Get sensors for this device
                sensors = device_info.get('sensors', [])
                for sensor_path in sensors:
                    if sensor_path in self.simulators:
                        simulator = self.simulators[sensor_path]

                        # Get tag name (CamelCase conversion)
                        tag_name = sensor_path.split('/')[-1]
                        tag_name = ''.join(word.capitalize() for word in tag_name.split('_'))

                        # Create tag node
                        tag_node = await device_node.add_variable(
                            idx,
                            tag_name,
                            simulator.get_value(),
                            varianttype=ua.VariantType.Double,
                        )
                        await tag_node.set_writable()

                        # Store with vendor-specific path
                        vendor_path = f"vendor_kepware_{channel_name}_{device_name}_{tag_name}"
                        self.nodes[vendor_path] = tag_node

        logger.info(f"    Created Kepware structure: {len(channels)} channels")

    async def _create_sparkplug_nodes(self, idx: int, parent: Node, mode):
        """Create Sparkplug B Group/EdgeNode/Device structure."""
        # Sparkplug B is primarily MQTT-based, but we create OPC UA nodes for reference
        group_id = getattr(mode, 'group_id', 'DatabricksDemo')
        edge_node_id = getattr(mode, 'edge_node_id', 'OTSimulator01')

        # Create group node
        group_node = await parent.add_object(idx, group_id)
        edge_node = await group_node.add_object(idx, edge_node_id)

        # Get devices
        devices = getattr(mode, 'devices', {})
        for device_name, device_info in devices.items():
            device_node = await edge_node.add_object(idx, device_name)

            sensors = device_info.get('sensors', [])
            for sensor_path in sensors:
                if sensor_path in self.simulators:
                    simulator = self.simulators[sensor_path]

                    # Get metric name
                    metric_name = sensor_path.replace('/', '/')

                    # Create metric node
                    metric_node = await device_node.add_variable(
                        idx,
                        metric_name,
                        simulator.get_value(),
                        varianttype=ua.VariantType.Double,
                    )
                    await metric_node.set_writable()

                    # Store with vendor-specific path
                    vendor_path = f"vendor_sparkplug_{device_name}_{metric_name}"
                    self.nodes[vendor_path] = metric_node

        logger.info(f"    Created Sparkplug B structure: {len(devices)} devices")

    async def _create_honeywell_nodes(self, idx: int, parent: Node, mode):
        """Create Honeywell Experion Server.Module.Point structure with composite attributes."""
        server_name = getattr(mode, 'server_name', 'EXPERION_PKS')
        server_node = await parent.add_object(idx, server_name)

        # Get modules
        modules = getattr(mode, 'modules', {})
        for module_name, module_info in modules.items():
            module_node = await server_node.add_object(idx, module_name)

            points = module_info.get('points', [])
            for sensor_path in points:
                if sensor_path in self.simulators:
                    simulator = self.simulators[sensor_path]

                    # Get abbreviated point name
                    point_name = sensor_path.split('/')[-1].upper()
                    # Abbreviate if needed (e.g., CRUSHER -> CRUSH)
                    if len(point_name) > 12:
                        point_name = point_name[:12]

                    # Create point folder
                    point_node = await module_node.add_object(idx, point_name)

                    # Create composite attributes (PV, PVEUHI, PVEULO, etc.)
                    value = simulator.get_value()
                    config = simulator.config

                    # PV (Process Value)
                    pv_node = await point_node.add_variable(
                        idx, "PV", value, varianttype=ua.VariantType.Double
                    )
                    await pv_node.set_writable()

                    # PVEUHI (Engineering Units High)
                    await point_node.add_variable(
                        idx, "PVEUHI", config.max_value, varianttype=ua.VariantType.Double
                    )

                    # PVEULO (Engineering Units Low)
                    await point_node.add_variable(
                        idx, "PVEULO", config.min_value, varianttype=ua.VariantType.Double
                    )

                    # PVUNITS (Engineering Units)
                    await point_node.add_variable(
                        idx, "PVUNITS", config.unit, varianttype=ua.VariantType.String
                    )

                    # PVBAD (Bad quality flag)
                    await point_node.add_variable(
                        idx, "PVBAD", False, varianttype=ua.VariantType.Boolean
                    )

                    # Store PV node for updates
                    vendor_path = f"vendor_honeywell_{module_name}_{point_name}_PV"
                    self.nodes[vendor_path] = pv_node

        logger.info(f"    Created Honeywell structure: {len(modules)} modules")

    async def _create_generic_nodes(self, idx: int, parent: Node, mode):
        """Create Generic vendor mode structure (simple flat structure)."""
        # Group by industry
        for industry in self.industries:
            industry_name = industry.value if hasattr(industry, 'value') else industry
            industry_node = await parent.add_object(idx, industry_name)

            for sensor_path, simulator in self.simulators.items():
                if sensor_path.startswith(f"{industry_name}/"):
                    sensor_name = sensor_path.split('/')[-1]

                    # Create sensor node
                    sensor_node = await industry_node.add_variable(
                        idx,
                        sensor_name,
                        simulator.get_value(),
                        varianttype=ua.VariantType.Double,
                    )
                    await sensor_node.set_writable()

                    # Store with vendor-specific path
                    vendor_path = f"vendor_generic_{industry_name}_{sensor_name}"
                    self.nodes[vendor_path] = sensor_node

        logger.info(f"    Created Generic structure for {len(self.industries)} industries")

    async def _run_server_loop(self):
        """Internal method: Run the OPC-UA server update loop."""
        async with self.server:
            logger.info(f"OPC-UA server started at {self.endpoint}")
            self._running = True

            # Register with discovery server for network discovery
            try:
                await self.server.register_to_discovery()
                logger.info(f"✓ Registered to discovery server at opc.tcp://localhost:4840")
            except Exception as e:
                logger.warning(f"Could not register to discovery server: {e}")
                logger.info("Server will still be accessible via direct endpoint connection")

            # Log once that update loop started
            logger.info(f"Starting sensor value update loop (2 Hz) for {len(self.simulators)} sensors...")

            try:
                iteration_count = 0
                while self._running:
                    iteration_count += 1
                    # Log every 100 iterations (every 50 seconds at 2 Hz)
                    if iteration_count % 100 == 0:
                        logger.debug(f"Update loop iteration {iteration_count}, updating {len(self.simulators)} sensors")

                    # Update all sensors (with PLC metadata if enabled)
                    for path, simulator in self.simulators.items():
                        # Get value through PLC layer if available
                        if self.simulator_manager and hasattr(self.simulator_manager, 'get_sensor_value_with_plc'):
                            result = self.simulator_manager.get_sensor_value_with_plc(path)
                            new_value = result.get('value')
                            # TODO: Update quality code in OPC-UA node (requires StatusCode handling)
                        else:
                            new_value = simulator.update()

                        # Ensure value is float for OPC-UA Double type
                        if new_value is not None:
                            new_value = float(new_value)
                            node = self.nodes[path]
                            await node.write_value(new_value)

                    # Update PLC diagnostic nodes if in PLC mode
                    if self.simulator_manager and hasattr(self.simulator_manager, 'plc_manager'):
                        plc_manager = self.simulator_manager.plc_manager
                        if plc_manager and plc_manager.enabled:
                            all_diag = plc_manager.get_all_diagnostics()
                            for plc_name, diag in all_diag.items():
                                counters = diag.get('counters', {})

                                # Update scan count (Int64)
                                scan_count_key = f"_diag_{plc_name}_scan_count"
                                if scan_count_key in self.nodes:
                                    try:
                                        total_scans = counters.get('total_scans', 0)
                                        await self.nodes[scan_count_key].write_value(ua.DataValue(ua.Variant(total_scans, ua.VariantType.Int64)))
                                    except Exception as e:
                                        pass  # Silently ignore diagnostic update errors

                                # Update forced values count (Int32)
                                forced_count_key = f"_diag_{plc_name}_forced_count"
                                if forced_count_key in self.nodes:
                                    try:
                                        forced_count = counters.get('forced_values_count', 0)
                                        await self.nodes[forced_count_key].write_value(ua.DataValue(ua.Variant(forced_count, ua.VariantType.Int32)))
                                    except Exception as e:
                                        pass  # Silently ignore diagnostic update errors

                    # Update frequency - adjust based on update_frequency_hz from configs
                    await asyncio.sleep(0.5)  # 2 Hz update rate

            except asyncio.CancelledError:
                logger.info("OPC-UA server stopping...")
                self._running = False
            except Exception as e:
                logger.exception(f"Error in OPC-UA server: {e}")
                raise

    async def start(self):
        """Start the OPC-UA server as a background task."""
        if self._running:
            logger.warning("OPC-UA server already running")
            return

        # Always initialize if not yet initialized (ensures nodes are created)
        if not self._initialized:
            logger.info("Initializing OPC-UA server with sensor nodes...")
            await self.init()

        # Create background task instead of blocking
        self._server_task = asyncio.create_task(self._run_server_loop())
        logger.info("OPC-UA server task created")

        # Give it a moment to start
        await asyncio.sleep(0.1)

    async def reinitialize_with_plcs(self):
        """Reinitialize OPC-UA server with PLC-based node structure.

        This is called after PLC manager is initialized to rebuild the node tree
        with PLC hierarchy instead of direct sensor structure.
        """
        if not self.server:
            logger.warning("Cannot reinitialize - server not created")
            return

        if self._running:
            logger.info("Stopping OPC-UA server for reinitialization with PLCs...")
            self._running = False
            if self._server_task and not self._server_task.done():
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass

            # Give server time to fully stop
            await asyncio.sleep(0.5)

        logger.info("Rebuilding OPC-UA nodes with PLC hierarchy...")

        # Clear existing nodes and simulators
        self.nodes.clear()
        self.simulators.clear()

        # Re-run initialization (will detect PLC manager and use PLC mode)
        self._initialized = False
        await self.init()

        # Restart server
        self._server_task = asyncio.create_task(self._run_server_loop())
        logger.info("✓ OPC-UA server reinitialized with PLC-based nodes")

    async def stop(self):
        """Stop the OPC-UA server."""
        self._running = False
        if self.server:
            await self.server.stop()
        # Reset initialization flag to allow re-initialization on next start
        self._initialized = False
        self.server = None

    def inject_fault(self, sensor_path: str, duration: float = 10.0):
        """Inject a fault into a specific sensor."""
        if sensor_path in self.simulators:
            self.simulators[sensor_path].inject_fault(duration)
            logger.info(f"Fault injected into {sensor_path} for {duration} seconds")
        else:
            logger.warning(f"Sensor {sensor_path} not found")


async def run_opcua_simulator(
    endpoint: str = "opc.tcp://0.0.0.0:4840/freeopcua/server/",
    industries: list[IndustryType] | None = None,
):
    """Run OPC-UA simulator (convenience function)."""
    sim = OPCUASimulator(endpoint=endpoint, industries=industries)
    await sim.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run with all industries
    asyncio.run(run_opcua_simulator())
