"""Integration layer between vendor modes and OT simulator infrastructure.

This module extends the existing simulator infrastructure to support multiple
vendor-specific output formats simultaneously.
"""

from __future__ import annotations

import asyncio
import logging
import time
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from ot_simulator.plc_models import PLCSimulator, PLCQualityCode, PLCConfig, PLCVendor
from ot_simulator.sensor_models import SensorSimulator
from ot_simulator.vendor_modes.base import ModeConfig, VendorModeType
from ot_simulator.vendor_modes.factory import VendorModeFactory, VendorModeManager

logger = logging.getLogger("ot_simulator.vendor_integration")


class VendorModeIntegration:
    """Integrates vendor modes with existing simulator infrastructure."""

    def __init__(self, simulator_manager, config_path: Optional[str] = None):
        """Initialize vendor mode integration.

        Args:
            simulator_manager: Reference to SimulatorManager instance
            config_path: Path to vendor modes config file
        """
        self.simulator_manager = simulator_manager
        self.config_path = config_path or Path(__file__).parent / "config.yaml"
        self.mode_manager = VendorModeManager()

        # Track which sensors have been registered with which modes
        self.sensor_registrations: Dict[str, List[VendorModeType]] = {}

        # Message buffer for live inspector (circular buffer)
        from collections import deque
        self.message_buffer = deque(maxlen=2000)  # Keep last 2000 messages (large buffer for all protocols)

        # Track active MQTT topics being published
        self.active_topics: Dict[str, Dict[str, Any]] = {}  # topic -> {mode, last_publish_time, message_count}

    async def initialize(self):
        """Initialize vendor modes from configuration."""
        logger.info("Initializing vendor mode integration...")

        # Load configuration
        mode_configs = self._load_config()

        # Initialize mode manager
        await self.mode_manager.initialize(mode_configs)

        # Auto-register existing sensors with all enabled modes
        if self._get_global_config().get("auto_register", True):
            await self._auto_register_sensors()

        logger.info("Vendor mode integration initialized")

    async def shutdown(self):
        """Shutdown vendor mode integration."""
        logger.info("Shutting down vendor mode integration...")
        await self.mode_manager.shutdown()

    def _load_config(self) -> List[ModeConfig]:
        """Load vendor mode configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                config_data = yaml.safe_load(f)

            mode_configs = []
            vendor_modes = config_data.get("vendor_modes", {})

            for mode_type_str, mode_cfg in vendor_modes.items():
                try:
                    mode_type = VendorModeType(mode_type_str)
                except ValueError:
                    logger.warning(f"Unknown mode type in config: {mode_type_str}")
                    continue

                config = ModeConfig(
                    mode_type=mode_type,
                    enabled=mode_cfg.get("enabled", False),
                    opcua_enabled=mode_cfg.get("opcua_enabled", True),
                    opcua_port=mode_cfg.get("opcua_port"),
                    mqtt_enabled=mode_cfg.get("mqtt_enabled", True),
                    mqtt_topic_prefix=mode_cfg.get("mqtt_topic_prefix"),
                    settings=mode_cfg.get("settings", {}),
                )

                mode_configs.append(config)

            logger.info(f"Loaded configuration for {len(mode_configs)} vendor modes")
            return mode_configs

        except Exception as e:
            logger.error(f"Failed to load vendor mode config: {e}", exc_info=True)
            return []

    def _get_global_config(self) -> Dict[str, Any]:
        """Get global configuration settings."""
        try:
            with open(self.config_path, "r") as f:
                config_data = yaml.safe_load(f)
            return config_data.get("global", {})
        except:
            return {}

    async def _auto_register_sensors(self):
        """Auto-register all existing sensors with enabled modes."""
        logger.info("Auto-registering sensors with vendor modes...")

        count = 0
        for sensor_path, sensor in self.simulator_manager.sensor_instances.items():
            await self.register_sensor(sensor_path, sensor)
            count += 1

        logger.info(f"Auto-registered {count} sensors with vendor modes")

    async def register_sensor(
        self,
        sensor_path: str,
        sensor: SensorSimulator,
    ):
        """Register a sensor with all enabled vendor modes.

        Args:
            sensor_path: Full sensor path (e.g., "mining/crusher_1_motor_power")
            sensor: SensorSimulator instance
        """
        # Parse sensor path
        parts = sensor_path.split("/")
        if len(parts) != 2:
            logger.warning(f"Invalid sensor path format: {sensor_path}")
            return

        industry, sensor_name = parts

        # Get PLC instance for this sensor (if PLC manager enabled)
        plc_instance = None
        if self.simulator_manager.plc_manager:
            # Find which PLC handles this sensor
            plc_instance = self.simulator_manager.plc_manager.get_plc_for_sensor(sensor_path)

        # Register with each enabled mode
        for mode in self.mode_manager.get_active_modes():
            try:
                mode_type = mode.config.mode_type

                # Mode-specific registration
                if mode_type == VendorModeType.KEPWARE:
                    if plc_instance:
                        mode.register_sensor(sensor_name, plc_instance, industry)
                    else:
                        logger.debug(f"Skipping Kepware registration for {sensor_name} (no PLC)")

                elif mode_type == VendorModeType.SPARKPLUG_B:
                    if plc_instance:
                        mode.register_sensor(
                            sensor_name,
                            plc_instance,
                            industry,
                            sensor.config.sensor_type.value,
                            sensor.config.unit,
                        )
                    else:
                        logger.debug(f"Skipping Sparkplug B registration for {sensor_name} (no PLC)")

                elif mode_type == VendorModeType.HONEYWELL:
                    if plc_instance:
                        mode.register_sensor(sensor_name, plc_instance, sensor.config)
                    else:
                        logger.debug(f"Skipping Honeywell registration for {sensor_name} (no PLC)")

                # Track registration
                if sensor_path not in self.sensor_registrations:
                    self.sensor_registrations[sensor_path] = []
                self.sensor_registrations[sensor_path].append(mode_type)

            except Exception as e:
                logger.error(
                    f"Failed to register {sensor_path} with {mode.config.mode_type}: {e}"
                )

    def format_sensor_data(
        self,
        sensor_path: str,
        value: float,
        quality: PLCQualityCode,
        timestamp: Optional[float] = None,
        **metadata
    ) -> Dict[VendorModeType, Dict[str, Any]]:
        """Format sensor data for all enabled vendor modes.

        Args:
            sensor_path: Full sensor path
            value: Sensor value
            quality: PLC quality code
            timestamp: Timestamp (defaults to current time)
            metadata: Additional metadata

        Returns:
            Dictionary mapping mode type to formatted data
        """
        if timestamp is None:
            timestamp = time.time()

        # Parse sensor path
        parts = sensor_path.split("/")
        if len(parts) != 2:
            return {}

        industry, sensor_name = parts

        # Get sensor instance for metadata
        sensor = self.simulator_manager.sensor_instances.get(sensor_path)
        if sensor:
            metadata.setdefault("unit", sensor.config.unit)
            metadata.setdefault("sensor_type", sensor.config.sensor_type.value)

        metadata["industry"] = industry

        # Get PLC instance
        plc_instance = None
        if self.simulator_manager.plc_manager:
            plc_instance = self.simulator_manager.plc_manager.get_plc_for_sensor(sensor_path)

        if not plc_instance:
            logger.debug(f"No PLC instance for {sensor_path}, using generic mode only")
            # Can still format for generic mode without PLC
            # Create a dummy PLC instance for generic mode
            from ot_simulator.plc_models import PLCConfig, PLCVendor
            plc_config = PLCConfig(
                vendor=PLCVendor.SIEMENS,
                model="Generic",
                name="GENERIC_PLC",
            )
            plc_instance = PLCSimulator(plc_config, self.simulator_manager)

        # Format for each enabled mode
        formatted_data = {}
        for mode in self.mode_manager.get_active_modes():
            try:
                data = mode.format_sensor_data(
                    sensor_name,
                    value,
                    quality,
                    timestamp,
                    plc_instance,
                    **metadata
                )

                if data:  # Only include if mode returned data (e.g., Sparkplug B COV may skip)
                    formatted_data[mode.config.mode_type] = data

            except Exception as e:
                logger.error(
                    f"Failed to format {sensor_path} for {mode.config.mode_type}: {e}"
                )

        return formatted_data

    def get_opcua_node_id(
        self,
        sensor_path: str,
        mode_type: VendorModeType = VendorModeType.GENERIC,
    ) -> Optional[str]:
        """Get OPC UA node ID for a sensor in a specific mode.

        Args:
            sensor_path: Full sensor path
            mode_type: Vendor mode type

        Returns:
            OPC UA node ID string or None
        """
        mode = self.mode_manager.get_mode(mode_type)
        if not mode:
            return None

        # Parse sensor path
        parts = sensor_path.split("/")
        if len(parts) != 2:
            return None

        industry, sensor_name = parts

        # Get PLC instance
        plc_instance = None
        if self.simulator_manager.plc_manager:
            plc_instance = self.simulator_manager.plc_manager.get_plc_for_sensor(sensor_path)

        if not plc_instance:
            # Create dummy PLC for generic mode
            plc_config = PLCConfig(
                vendor=PLCVendor.SIEMENS,
                model="Generic",
                name="GENERIC_PLC",
            )
            plc_instance = PLCSimulator(plc_config, self.simulator_manager)

        metadata = {"industry": industry}

        return mode.get_opcua_node_id(sensor_name, plc_instance, **metadata)

    def get_mqtt_topic(
        self,
        sensor_path: str,
        mode_type: VendorModeType = VendorModeType.GENERIC,
    ) -> Optional[str]:
        """Get MQTT topic for a sensor in a specific mode.

        Args:
            sensor_path: Full sensor path
            mode_type: Vendor mode type

        Returns:
            MQTT topic string or None
        """
        mode = self.mode_manager.get_mode(mode_type)
        if not mode:
            return None

        # Parse sensor path
        parts = sensor_path.split("/")
        if len(parts) != 2:
            return None

        industry, sensor_name = parts

        # Get PLC instance
        plc_instance = None
        if self.simulator_manager.plc_manager:
            plc_instance = self.simulator_manager.plc_manager.get_plc_for_sensor(sensor_path)

        if not plc_instance:
            # Create dummy PLC for generic mode
            plc_config = PLCConfig(
                vendor=PLCVendor.SIEMENS,
                model="Generic",
                name="GENERIC_PLC",
            )
            plc_instance = PLCSimulator(plc_config, self.simulator_manager)

        metadata = {"industry": industry}

        return mode.get_mqtt_topic(sensor_name, plc_instance, **metadata)

    def get_mode_diagnostics(self, mode_type: VendorModeType) -> Dict[str, Any]:
        """Get diagnostics for a specific mode."""
        mode = self.mode_manager.get_mode(mode_type)
        if not mode:
            return {"error": "Mode not active"}

        try:
            return mode.get_diagnostics()
        except Exception as e:
            logger.error(f"Failed to get diagnostics for {mode_type}: {e}")
            return {"error": str(e)}

    def get_all_mode_status(self) -> Dict[str, Any]:
        """Get status of all vendor modes."""
        return self.mode_manager.get_all_status()

    def get_mode_status(self, mode_type: VendorModeType) -> Dict[str, Any]:
        """Get status of a specific vendor mode."""
        all_status = self.mode_manager.get_all_status()
        return all_status.get(mode_type.value, {})

    def get_mode_diagnostics(self, mode_type: VendorModeType) -> Dict[str, Any]:
        """Get diagnostics for a specific vendor mode."""
        mode = self.mode_manager.get_mode(mode_type)
        if mode and hasattr(mode, 'get_diagnostics'):
            return mode.get_diagnostics()
        return {}

    async def enable_mode(self, mode_type: VendorModeType) -> bool:
        """Enable a vendor mode dynamically."""
        # Load config for this mode
        mode_configs = self._load_config()
        config = None
        for cfg in mode_configs:
            if cfg.mode_type == mode_type:
                config = cfg
                break

        if not config:
            logger.error(f"No configuration found for mode: {mode_type}")
            return False

        config.enabled = True
        success = await self.mode_manager.enable_mode(mode_type, config)

        if success:
            # Re-register all sensors with this mode
            await self._auto_register_sensors()

        return success

    async def disable_mode(self, mode_type: VendorModeType) -> bool:
        """Disable a vendor mode dynamically."""
        return await self.mode_manager.disable_mode(mode_type)

    def capture_message(self, mode_type: VendorModeType, topic: str, payload: Dict[str, Any], protocol: str = "mqtt", message_type: str = None):
        """Capture a vendor mode message for the live inspector.

        Args:
            mode_type: Type of vendor mode
            topic: MQTT topic or identifier
            payload: Message payload
            protocol: Source protocol (mqtt, opcua, modbus, etc.)
            message_type: Sparkplug B message type (NBIRTH, DBIRTH, NDATA, DDATA, etc.)
        """
        import time

        # Extract industry from sensor_path if available
        industry = None
        if isinstance(payload, dict):
            sensor_path = payload.get("sensor_path")
            if sensor_path and "/" in sensor_path:
                industry = sensor_path.split("/")[0]

        # Extract Sparkplug B message type from topic if not provided
        if not message_type and mode_type == VendorModeType.SPARKPLUG_B:
            # Topic format: spBv1.0/{group_id}/{message_type}/{edge_node_id}/{device_id}
            parts = topic.split("/")
            if len(parts) >= 3:
                message_type = parts[2]  # NBIRTH, DBIRTH, NDATA, DDATA, etc.

        message = {
            "timestamp": time.time(),
            "mode": mode_type.value,
            "topic": topic,
            "payload": payload,
            "protocol": protocol,
            "industry": industry,
            "message_type": message_type  # Add Sparkplug B message type
        }
        self.message_buffer.append(message)

        # Track topic for MQTT protocol
        if protocol == "mqtt" and topic:
            if topic not in self.active_topics:
                self.active_topics[topic] = {
                    "mode": mode_type.value,
                    "message_type": message_type,
                    "first_seen": time.time(),
                    "last_publish_time": time.time(),
                    "message_count": 0
                }
            self.active_topics[topic]["last_publish_time"] = time.time()
            self.active_topics[topic]["message_count"] += 1

    def get_active_topics(self) -> Dict[str, Any]:
        """Get currently active MQTT topics.

        Returns:
            Dictionary of topics with metadata including mode, message count, last publish time
        """
        import time
        current_time = time.time()

        # Build topic tree structure
        topic_tree = {}
        topic_list = []

        for topic, info in self.active_topics.items():
            # Calculate message rate (messages per second over last 60 seconds)
            time_since_first = current_time - info["first_seen"]
            message_rate = info["message_count"] / time_since_first if time_since_first > 0 else 0

            topic_data = {
                "topic": topic,
                "mode": info["mode"],
                "message_type": info.get("message_type"),
                "message_count": info["message_count"],
                "message_rate": round(message_rate, 2),
                "last_publish": current_time - info["last_publish_time"],  # seconds ago
            }
            topic_list.append(topic_data)

        # Sort by topic name
        topic_list.sort(key=lambda x: x["topic"])

        return {
            "topics": topic_list,
            "total_topics": len(topic_list),
            "by_mode": self._group_topics_by_mode()
        }

    def _group_topics_by_mode(self) -> Dict[str, int]:
        """Group topic counts by mode."""
        by_mode = {}
        for info in self.active_topics.values():
            mode = info["mode"]
            by_mode[mode] = by_mode.get(mode, 0) + 1
        return by_mode

    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from the buffer.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages (newest first)
        """
        # Return newest first
        messages = list(self.message_buffer)
        messages.reverse()
        return messages[:limit]
