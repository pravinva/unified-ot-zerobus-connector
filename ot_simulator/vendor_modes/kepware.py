"""Kepware KEPServerEX mode - Channel.Device.Tag structure.

Kepware is the world's leading OPC server (100K+ installations).
Format: Channel.Device.Tag structure with IoT Gateway JSON format.

Example OPC UA: ns=2;s=Siemens_S7_Crushing.Crusher_01.MotorPower
Example MQTT: kepware/Siemens_S7_Crushing/Crusher_01/MotorPower

MQTT Payload (IoT Gateway format):
{
  "timestamp": 1738851825000,  // Epoch milliseconds
  "values": [{
    "id": "Siemens_S7_Crushing.Crusher_01.MotorPower",
    "v": 850.3,
    "q": true,  // true=Good, false=Bad
    "t": 1738851825000
  }]
}
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ot_simulator.plc_models import PLCSimulator, PLCQualityCode, PLCVendor
from ot_simulator.vendor_modes.base import (
    ModeConfig,
    ModeStatus,
    VendorMode,
    VendorModeType,
)

logger = logging.getLogger("ot_simulator.kepware")


@dataclass
class KepwareChannel:
    """Represents a Kepware channel (connection to device)."""

    name: str
    driver_type: str  # e.g., "Siemens TCP/IP Ethernet", "Modbus TCP/IP"
    plc_vendor: PLCVendor
    plc_model: str
    devices: List[KepwareDevice] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "driver_type": self.driver_type,
            "plc_vendor": self.plc_vendor,
            "plc_model": self.plc_model,
            "device_count": len(self.devices),
            "tag_count": sum(len(d.tags) for d in self.devices),
        }


@dataclass
class KepwareDevice:
    """Represents a Kepware device (logical grouping of tags)."""

    name: str
    channel_name: str
    sensors: List[str] = field(default_factory=list)

    @property
    def tags(self) -> List[str]:
        """Get list of tag names (sensors)."""
        return self.sensors


class KepwareMode(VendorMode):
    """Kepware KEPServerEX mode implementation."""

    def __init__(self, config: ModeConfig):
        super().__init__(config)

        # Kepware-specific configuration
        self.iot_gateway_format = config.settings.get("iot_gateway_format", True)
        self.batch_by_device = config.settings.get("batch_by_device", True)

        # Channel/Device structure
        self.channels: Dict[str, KepwareChannel] = {}
        self.device_to_channel: Dict[str, str] = {}

        # Tag cache for fast lookup
        self.sensor_to_path: Dict[str, tuple[str, str, str]] = {}  # sensor -> (channel, device, tag)

    async def initialize(self) -> bool:
        """Initialize Kepware mode."""
        try:
            logger.info("Initializing Kepware mode...")

            # Build Channel/Device structure from configuration
            mappings = self.config.settings.get("channel_mappings", {})
            if not mappings:
                logger.warning("No channel mappings configured for Kepware mode")
                # Create default mapping
                self._create_default_mappings()
            else:
                self._load_channel_mappings(mappings)

            self.metrics.status = ModeStatus.ACTIVE
            logger.info(
                f"Kepware mode initialized: {len(self.channels)} channels, "
                f"{sum(len(c.devices) for c in self.channels.values())} devices"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Kepware mode: {e}", exc_info=True)
            self.metrics.status = ModeStatus.ERROR
            self.metrics.update_error(str(e))
            return False

    async def shutdown(self):
        """Shutdown Kepware mode."""
        logger.info("Shutting down Kepware mode...")
        self.metrics.status = ModeStatus.DISABLED

    def _create_default_mappings(self):
        """Create default channel/device mappings based on PLC assignments."""
        logger.info("Creating default Kepware mappings...")

        # Default channel per vendor
        vendor_channels = {
            PLCVendor.SIEMENS: "Siemens_S7_Crushing",
            PLCVendor.ROCKWELL: "AB_ControlLogix_Utilities",
            PLCVendor.SCHNEIDER: "Modbus_TCP_Wellheads",
            PLCVendor.ABB: "ABB_AC500_Manufacturing",
            PLCVendor.MITSUBISHI: "Mitsubishi_MELSEC_Assembly",
            PLCVendor.OMRON: "Omron_Sysmac_Packaging",
        }

        # Create one channel per vendor
        for vendor, channel_name in vendor_channels.items():
            driver_type = self._get_driver_type(vendor)
            channel = KepwareChannel(
                name=channel_name,
                driver_type=driver_type,
                plc_vendor=vendor,
                plc_model="Generic",
            )
            self.channels[channel_name] = channel

    def _load_channel_mappings(self, mappings: Dict[str, Any]):
        """Load channel mappings from configuration."""
        for channel_cfg in mappings.get("channels", []):
            # Get PLC vendor, default to siemens if not specified or invalid
            plc_vendor_str = channel_cfg.get("plc_vendor", "siemens")
            try:
                plc_vendor = PLCVendor(plc_vendor_str)
            except ValueError:
                logger.warning(f"Invalid PLC vendor '{plc_vendor_str}', defaulting to siemens")
                plc_vendor = PLCVendor.SIEMENS

            channel = KepwareChannel(
                name=channel_cfg["name"],
                driver_type=channel_cfg.get("driver_type", "Generic"),
                plc_vendor=plc_vendor,
                plc_model=channel_cfg.get("plc_model", "Generic"),
            )

            # Load devices for this channel
            for device_cfg in channel_cfg.get("devices", []):
                device = KepwareDevice(
                    name=device_cfg["name"],
                    channel_name=channel.name,
                    sensors=device_cfg.get("sensors", []),
                )
                channel.devices.append(device)
                self.device_to_channel[device.name] = channel.name

                # Build sensor to path cache
                for sensor in device.sensors:
                    tag_name = self._sensor_to_tag_name(sensor)
                    self.sensor_to_path[sensor] = (channel.name, device.name, tag_name)

            self.channels[channel.name] = channel

    def _get_driver_type(self, vendor: PLCVendor) -> str:
        """Get Kepware driver type for PLC vendor."""
        driver_map = {
            PLCVendor.SIEMENS: "Siemens TCP/IP Ethernet",
            PLCVendor.ROCKWELL: "Allen-Bradley ControlLogix Ethernet",
            PLCVendor.SCHNEIDER: "Modbus TCP/IP",
            PLCVendor.ABB: "ABB AC500",
            PLCVendor.MITSUBISHI: "Mitsubishi Ethernet",
            PLCVendor.OMRON: "Omron FINS/TCP",
        }
        return driver_map.get(vendor, "Generic")

    def _sensor_to_tag_name(self, sensor_name: str) -> str:
        """Convert sensor name to Kepware tag name (CamelCase).

        Example: crusher_1_motor_power -> MotorPower
        """
        # Remove equipment prefix (crusher_1_, conveyor_01_, etc.)
        parts = sensor_name.split("_")

        # Find where the actual measurement name starts
        # (after equipment identifier like crusher_1, conveyor_01)
        start_idx = 0
        for i, part in enumerate(parts):
            if part.isdigit() or (part and not part[0].isdigit()):
                if i > 0 and parts[i-1].isdigit():
                    start_idx = i
                    break

        # Convert to CamelCase
        measurement_parts = parts[start_idx:] if start_idx > 0 else parts
        tag_name = "".join(word.capitalize() for word in measurement_parts)
        return tag_name if tag_name else sensor_name

    def _get_device_from_sensor(self, sensor_name: str) -> str:
        """Extract device name from sensor name.

        Example: crusher_1_motor_power -> Crusher_01
        """
        parts = sensor_name.split("_")

        # Find equipment identifier (e.g., crusher_1, conveyor_01)
        equipment = []
        for i, part in enumerate(parts):
            if i == 0:
                equipment.append(part.capitalize())
            elif part.isdigit():
                equipment.append(f"{int(part):02d}")
                break
            else:
                equipment.append(part.capitalize())

        return "_".join(equipment) if equipment else "Device_01"

    def register_sensor(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        industry: str,
    ):
        """Register a sensor with Kepware mode.

        Args:
            sensor_name: Name of the sensor
            plc_instance: PLC instance reading this sensor
            industry: Industry this sensor belongs to
        """
        # Find or create channel for this PLC
        channel_name = None
        for ch in self.channels.values():
            if ch.plc_vendor == plc_instance.config.vendor:
                channel_name = ch.name
                break

        if not channel_name:
            # Create new channel
            channel_name = f"{plc_instance.config.vendor.value.capitalize()}_{industry.capitalize()}"
            channel = KepwareChannel(
                name=channel_name,
                driver_type=self._get_driver_type(plc_instance.config.vendor),
                plc_vendor=plc_instance.config.vendor,
                plc_model=plc_instance.config.model,
            )
            self.channels[channel_name] = channel

        # Find or create device for this sensor
        device_name = self._get_device_from_sensor(sensor_name)

        device = None
        for dev in self.channels[channel_name].devices:
            if dev.name == device_name:
                device = dev
                break

        if not device:
            device = KepwareDevice(
                name=device_name,
                channel_name=channel_name,
            )
            self.channels[channel_name].devices.append(device)
            self.device_to_channel[device_name] = channel_name

        # Add sensor to device
        if sensor_name not in device.sensors:
            device.sensors.append(sensor_name)

        # Update cache
        tag_name = self._sensor_to_tag_name(sensor_name)
        self.sensor_to_path[sensor_name] = (channel_name, device_name, tag_name)

    def format_sensor_data(
        self,
        sensor_name: str,
        value: float,
        quality: PLCQualityCode,
        timestamp: float,
        plc_instance: PLCSimulator,
        **metadata
    ) -> Dict[str, Any]:
        """Format sensor data in Kepware IoT Gateway JSON format."""

        # Get Channel.Device.Tag path
        if sensor_name in self.sensor_to_path:
            channel, device, tag = self.sensor_to_path[sensor_name]
        else:
            # Auto-register if not found
            self.register_sensor(sensor_name, plc_instance, metadata.get("industry", "unknown"))
            channel, device, tag = self.sensor_to_path[sensor_name]

        full_id = f"{channel}.{device}.{tag}"

        # Convert quality to boolean (Good=true, others=false)
        quality_good = quality in [PLCQualityCode.GOOD, PLCQualityCode.GOOD_LOCAL_OVERRIDE]

        # Kepware IoT Gateway format
        timestamp_ms = int(timestamp * 1000)

        if self.iot_gateway_format:
            formatted = {
                "timestamp": timestamp_ms,
                "values": [{
                    "id": full_id,
                    "v": value,
                    "q": quality_good,
                    "t": timestamp_ms,
                }]
            }
        else:
            # Simple JSON format
            formatted = {
                "id": full_id,
                "value": value,
                "quality": quality_good,
                "timestamp": timestamp_ms,
            }

        # Update metrics
        payload_size = len(json.dumps(formatted).encode("utf-8"))
        self.metrics.update_message_sent(payload_size, quality)

        return formatted

    def get_opcua_node_id(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Get OPC UA node ID in Kepware format.

        Example: ns=2;s=Siemens_S7_Crushing.Crusher_01.MotorPower
        """
        if sensor_name in self.sensor_to_path:
            channel, device, tag = self.sensor_to_path[sensor_name]
        else:
            self.register_sensor(sensor_name, plc_instance, metadata.get("industry", "unknown"))
            channel, device, tag = self.sensor_to_path[sensor_name]

        node_path = f"{channel}.{device}.{tag}"
        return f"ns=2;s={node_path}"

    def get_mqtt_topic(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Get MQTT topic in Kepware format.

        Example: kepware/Siemens_S7_Crushing/Crusher_01/MotorPower
        """
        if sensor_name in self.sensor_to_path:
            channel, device, tag = self.sensor_to_path[sensor_name]
        else:
            self.register_sensor(sensor_name, plc_instance, metadata.get("industry", "unknown"))
            channel, device, tag = self.sensor_to_path[sensor_name]

        prefix = self.config.mqtt_topic_prefix or "kepware"
        return f"{prefix}/{channel}/{device}/{tag}"

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get Kepware-specific diagnostics with device breakdown."""
        channel_stats = []
        for channel in self.channels.values():
            # Build device list for this channel
            devices_list = []
            for device in channel.devices:
                # Infer equipment type from device name
                equipment_type = "Generic Device"
                name_lower = device.name.lower()
                if "crusher" in name_lower:
                    equipment_type = "Primary Crusher" if "01" in device.name else "Secondary Crusher"
                elif "conveyor" in name_lower:
                    equipment_type = "Belt Conveyor"
                elif "pump" in name_lower:
                    equipment_type = "Pump"
                elif "motor" in name_lower:
                    equipment_type = "Motor"
                elif "turbine" in name_lower:
                    equipment_type = "Turbine"
                elif "compressor" in name_lower:
                    equipment_type = "Compressor"
                elif "reactor" in name_lower:
                    equipment_type = "Reactor"

                devices_list.append({
                    "name": device.name,
                    "equipment_type": equipment_type,
                    "tag_count": len(device.tags),
                    "status": "🟢 Active"  # All devices active in simulator
                })

            channel_stats.append({
                "name": channel.name,
                "driver_type": channel.driver_type,
                "plc_vendor": channel.plc_vendor.value if hasattr(channel.plc_vendor, 'value') else str(channel.plc_vendor),
                "plc_model": channel.plc_model,
                "device_count": len(channel.devices),
                "tag_count": sum(len(d.tags) for d in channel.devices),
                "devices": devices_list  # Add device breakdown
            })

        return {
            "channels": channel_stats,
            "total_channels": len(self.channels),
            "total_devices": sum(len(c.devices) for c in self.channels.values()),
            "total_tags": sum(
                sum(len(d.tags) for d in c.devices)
                for c in self.channels.values()
            ),
            "iot_gateway_format": self.iot_gateway_format,
            "batch_by_device": self.batch_by_device,
        }
