"""Base classes for vendor-specific output modes."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ot_simulator.plc_models import PLCQualityCode, PLCSimulator


class VendorModeType(str, Enum):
    """Supported vendor mode types."""

    GENERIC = "generic"
    KEPWARE = "kepware"
    SPARKPLUG_B = "sparkplug_b"
    HONEYWELL = "honeywell"
    PI_SYSTEM = "pi_system"
    AZURE_IOT = "azure_iot"


class ModeStatus(str, Enum):
    """Vendor mode operational status."""

    DISABLED = "disabled"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class ModeConfig:
    """Configuration for a vendor mode."""

    mode_type: VendorModeType
    enabled: bool = True

    # Protocol settings
    opcua_enabled: bool = True
    opcua_port: Optional[int] = None
    mqtt_enabled: bool = True
    mqtt_topic_prefix: Optional[str] = None

    # Mode-specific settings (override in subclasses)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModeMetrics:
    """Metrics for a vendor mode."""

    mode_type: VendorModeType
    status: ModeStatus

    # Message statistics
    messages_sent: int = 0
    messages_failed: int = 0
    bytes_sent: int = 0

    # Quality statistics
    good_quality_count: int = 0
    bad_quality_count: int = 0
    uncertain_quality_count: int = 0

    # Timing
    uptime_seconds: float = 0.0
    last_message_time: Optional[float] = None
    avg_message_rate: float = 0.0

    # Errors
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None

    def update_message_sent(self, size_bytes: int, quality: PLCQualityCode):
        """Update metrics after sending a message."""
        self.messages_sent += 1
        self.bytes_sent += size_bytes
        self.last_message_time = time.time()

        # Update quality statistics
        if quality in [PLCQualityCode.GOOD, PLCQualityCode.GOOD_LOCAL_OVERRIDE]:
            self.good_quality_count += 1
        elif quality == PLCQualityCode.UNCERTAIN:
            self.uncertain_quality_count += 1
        else:
            self.bad_quality_count += 1

    def update_error(self, error_message: str):
        """Update error metrics."""
        self.error_count += 1
        self.last_error = error_message
        self.last_error_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        total_quality = (
            self.good_quality_count +
            self.bad_quality_count +
            self.uncertain_quality_count
        )

        return {
            "mode_type": self.mode_type,
            "status": self.status,
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "bytes_sent": self.bytes_sent,
            "quality_distribution": {
                "good": self.good_quality_count,
                "bad": self.bad_quality_count,
                "uncertain": self.uncertain_quality_count,
                "good_percentage": (
                    (self.good_quality_count / total_quality * 100)
                    if total_quality > 0 else 0.0
                ),
            },
            "uptime_seconds": self.uptime_seconds,
            "last_message_time": self.last_message_time,
            "avg_message_rate": self.avg_message_rate,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time,
        }


class VendorMode(ABC):
    """Abstract base class for vendor-specific output modes."""

    def __init__(self, config: ModeConfig):
        self.config = config
        self.metrics = ModeMetrics(
            mode_type=config.mode_type,
            status=ModeStatus.DISABLED if not config.enabled else ModeStatus.INITIALIZING,
        )
        self.start_time = time.time()

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the vendor mode.

        Returns:
            True if initialization successful, False otherwise.
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """Shutdown the vendor mode and cleanup resources."""
        pass

    @abstractmethod
    def format_sensor_data(
        self,
        sensor_name: str,
        value: float,
        quality: PLCQualityCode,
        timestamp: float,
        plc_instance: PLCSimulator,
        **metadata
    ) -> Dict[str, Any]:
        """Format sensor data according to vendor specifications.

        Args:
            sensor_name: Name of the sensor
            value: Sensor value
            quality: PLC quality code
            timestamp: Timestamp of the reading
            plc_instance: PLC instance that read the sensor
            metadata: Additional metadata (unit, sensor_type, etc.)

        Returns:
            Formatted data dictionary ready for transmission.
        """
        pass

    @abstractmethod
    def get_opcua_node_id(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Get OPC UA node ID for a sensor in vendor format.

        Args:
            sensor_name: Name of the sensor
            plc_instance: PLC instance
            metadata: Additional metadata

        Returns:
            OPC UA node ID string (e.g., "ns=2;s=Channel.Device.Tag")
        """
        pass

    @abstractmethod
    def get_mqtt_topic(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Get MQTT topic for a sensor in vendor format.

        Args:
            sensor_name: Name of the sensor
            plc_instance: PLC instance
            metadata: Additional metadata

        Returns:
            MQTT topic string (e.g., "kepware/Channel/Device/Tag")
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the vendor mode.

        Returns:
            Status dictionary including metrics and configuration.
        """
        self.metrics.uptime_seconds = time.time() - self.start_time

        if self.metrics.uptime_seconds > 0:
            self.metrics.avg_message_rate = (
                self.metrics.messages_sent / self.metrics.uptime_seconds
            )

        return {
            "config": {
                "mode_type": self.config.mode_type,
                "enabled": self.config.enabled,
                "opcua_enabled": self.config.opcua_enabled,
                "opcua_port": self.config.opcua_port,
                "mqtt_enabled": self.config.mqtt_enabled,
                "mqtt_topic_prefix": self.config.mqtt_topic_prefix,
                "settings": self.config.settings,
            },
            "metrics": self.metrics.to_dict(),
        }

    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration dynamically.

        Args:
            new_config: New configuration settings.
        """
        if "enabled" in new_config:
            self.config.enabled = new_config["enabled"]
            self.metrics.status = (
                ModeStatus.ACTIVE if new_config["enabled"] else ModeStatus.DISABLED
            )

        if "opcua_enabled" in new_config:
            self.config.opcua_enabled = new_config["opcua_enabled"]

        if "mqtt_enabled" in new_config:
            self.config.mqtt_enabled = new_config["mqtt_enabled"]

        if "settings" in new_config:
            self.config.settings.update(new_config["settings"])
