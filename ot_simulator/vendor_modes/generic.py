"""Generic mode - Simple JSON/OPC UA structure (default).

This is the basic mode that provides simple, flat structures:
- OPC UA: ns=2;s=Industries/{industry}/{sensor_name}
- MQTT: sensors/{industry}/{sensor_name}/value

JSON format:
{
  "sensor": "crusher_1_motor_power",
  "value": 850.3,
  "unit": "kW",
  "quality": "Good",
  "timestamp": 1738851825.123,
  "industry": "mining",
  "plc": "PLC_MINING_CRUSH"
}
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from ot_simulator.plc_models import PLCSimulator, PLCQualityCode
from ot_simulator.vendor_modes.base import (
    ModeConfig,
    ModeStatus,
    VendorMode,
    VendorModeType,
)

logger = logging.getLogger("ot_simulator.generic")


class GenericMode(VendorMode):
    """Generic mode - simple JSON/OPC UA format."""

    def __init__(self, config: ModeConfig):
        super().__init__(config)

    async def initialize(self) -> bool:
        """Initialize generic mode."""
        logger.info("Initializing Generic mode...")
        self.metrics.status = ModeStatus.ACTIVE
        return True

    async def shutdown(self):
        """Shutdown generic mode."""
        logger.info("Shutting down Generic mode...")
        self.metrics.status = ModeStatus.DISABLED

    def format_sensor_data(
        self,
        sensor_name: str,
        value: float,
        quality: PLCQualityCode,
        timestamp: float,
        plc_instance: PLCSimulator,
        **metadata
    ) -> Dict[str, Any]:
        """Format sensor data in simple JSON format."""
        formatted = {
            "sensor": sensor_name,
            "value": value,
            "unit": metadata.get("unit", ""),
            "quality": quality.value,
            "timestamp": timestamp,
            "industry": metadata.get("industry", "unknown"),
            "plc": plc_instance.config.name,
            "plc_vendor": plc_instance.config.vendor.value,
            "sensor_type": metadata.get("sensor_type", "unknown"),
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
        """Get OPC UA node ID in generic format.

        Example: ns=2;s=Industries/mining/crusher_1_motor_power
        """
        industry = metadata.get("industry", "unknown")
        return f"ns=2;s=Industries/{industry}/{sensor_name}"

    def get_mqtt_topic(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Get MQTT topic in generic format.

        Example: sensors/mining/crusher_1_motor_power/value
        """
        industry = metadata.get("industry", "unknown")
        prefix = self.config.mqtt_topic_prefix or "sensors"
        return f"{prefix}/{industry}/{sensor_name}/value"

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get generic mode diagnostics."""
        return {
            "mode": "generic",
            "description": "Simple JSON/OPC UA format",
            "opcua_namespace": "ns=2;s=Industries/{industry}/{sensor}",
            "mqtt_topic": "sensors/{industry}/{sensor}/value",
        }
