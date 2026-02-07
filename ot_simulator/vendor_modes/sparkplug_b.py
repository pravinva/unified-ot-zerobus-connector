"""Sparkplug B mode - Eclipse IoT standard for MQTT.

Sparkplug B is an industrial IoT protocol specification that provides:
- Structured namespace: spBv1.0/{group_id}/{message_type}/{edge_node_id}/{device_id}
- Birth/Death certificates (NBIRTH, DBIRTH, NDEATH, DDEATH)
- Sequence numbers for message ordering
- Metric definitions with datatypes
- Quality codes and properties

Reference: https://www.eclipse.org/tahu/spec/Sparkplug%20Topic%20Namespace%20and%20State%20ManagementV2.2-with%20appendix%20B%20format%20-%20Eclipse.pdf
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ot_simulator.plc_models import PLCSimulator, PLCQualityCode, PLCRunMode
from ot_simulator.vendor_modes.base import (
    ModeConfig,
    ModeStatus,
    VendorMode,
    VendorModeType,
)

logger = logging.getLogger("ot_simulator.sparkplug_b")


class SparkplugMessageType(str, Enum):
    """Sparkplug B message types."""

    NBIRTH = "NBIRTH"  # Edge Node Birth Certificate
    NDEATH = "NDEATH"  # Edge Node Death Certificate
    DBIRTH = "DBIRTH"  # Device Birth Certificate
    DDEATH = "DDEATH"  # Device Death Certificate
    NDATA = "NDATA"  # Edge Node Data
    DDATA = "DDATA"  # Device Data
    NCMD = "NCMD"  # Edge Node Command
    DCMD = "DCMD"  # Device Command


class SparkplugDataType(Enum):
    """Sparkplug B data types."""

    INT8 = 1
    INT16 = 2
    INT32 = 3
    INT64 = 4
    UINT8 = 5
    UINT16 = 6
    UINT32 = 7
    UINT64 = 8
    FLOAT = 9
    DOUBLE = 10
    BOOLEAN = 11
    STRING = 12
    DATETIME = 13


@dataclass
class SparkplugMetric:
    """Sparkplug B metric definition."""

    name: str
    datatype: SparkplugDataType
    value: Any
    timestamp: int  # Milliseconds since epoch
    quality: int = 192  # 192 = Good (OPC UA quality code)
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Sparkplug B metric format."""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "dataType": self.datatype.name,
            "value": self.value,
            "properties": {
                "Quality": self.quality,
                **self.properties
            }
        }


@dataclass
class SparkplugDevice:
    """Represents a Sparkplug B device."""

    device_id: str
    metrics: List[SparkplugMetric] = field(default_factory=list)
    is_online: bool = False
    last_birth_seq: Optional[int] = None
    last_data_seq: Optional[int] = None

    def get_metric_names(self) -> List[str]:
        """Get list of metric names for this device."""
        return [m.name for m in self.metrics]


class SparkplugBMode(VendorMode):
    """Sparkplug B mode implementation."""

    def __init__(self, config: ModeConfig):
        super().__init__(config)

        # Sparkplug B configuration
        self.group_id = config.settings.get("group_id", "DatabricksDemo")
        self.edge_node_id = config.settings.get("edge_node_id", "OTSimulator01")
        self.use_protobuf = config.settings.get("use_protobuf", False)

        # Birth/Death sequence (bdSeq)
        self.bd_seq = 0

        # Message sequence (seq) - rolls over at 256
        self.msg_seq = 0

        # Device registry
        self.devices: Dict[str, SparkplugDevice] = {}

        # Edge node state
        self.edge_node_online = False
        self.edge_node_birth_time: Optional[float] = None

        # Metric definitions
        self.metric_definitions: Dict[str, SparkplugDataType] = {}

        # Change of Value tracking (for efficient publishing)
        self.last_values: Dict[str, float] = {}
        self.cov_threshold = config.settings.get("cov_threshold", 0.01)  # 1% change

    async def initialize(self) -> bool:
        """Initialize Sparkplug B mode."""
        try:
            logger.info(f"Initializing Sparkplug B mode: {self.group_id}/{self.edge_node_id}")

            # Initialize bdSeq
            self.bd_seq = 0
            self.msg_seq = 0

            # Load device mappings from configuration
            device_mappings = self.config.settings.get("device_mappings", {})
            if not device_mappings:
                logger.warning("No device mappings configured, using defaults")
                self._create_default_devices()
            else:
                self._load_device_mappings(device_mappings)

            self.metrics.status = ModeStatus.ACTIVE
            logger.info(
                f"Sparkplug B mode initialized: {len(self.devices)} devices, "
                f"bdSeq={self.bd_seq}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Sparkplug B mode: {e}", exc_info=True)
            self.metrics.status = ModeStatus.ERROR
            self.metrics.update_error(str(e))
            return False

    async def shutdown(self):
        """Shutdown Sparkplug B mode."""
        logger.info("Shutting down Sparkplug B mode...")

        # Send NDEATH message before shutdown
        if self.edge_node_online:
            self._generate_ndeath()

        self.edge_node_online = False
        self.metrics.status = ModeStatus.DISABLED

    def _create_default_devices(self):
        """Create default device groupings by industry."""
        default_devices = {
            "MiningAssets": ["mining"],
            "PowerGrid": ["utilities"],
            "ProductionLine": ["manufacturing"],
            "PipelineMonitor": ["oil_gas"],
        }

        for device_id, industries in default_devices.items():
            device = SparkplugDevice(
                device_id=device_id,
                is_online=False,
            )
            self.devices[device_id] = device

    def _load_device_mappings(self, mappings: Dict[str, Any]):
        """Load device mappings from configuration."""
        for device_id, device_cfg in mappings.items():
            device = SparkplugDevice(
                device_id=device_id,
                is_online=False,
            )
            self.devices[device_id] = device

    def _get_device_for_sensor(self, sensor_name: str, industry: str) -> str:
        """Determine which device a sensor belongs to."""
        # Map industry to device
        industry_to_device = {
            "mining": "MiningAssets",
            "utilities": "PowerGrid",
            "manufacturing": "ProductionLine",
            "oil_gas": "PipelineMonitor",
        }

        device_id = industry_to_device.get(industry, "GenericDevice")

        # Ensure device exists
        if device_id not in self.devices:
            self.devices[device_id] = SparkplugDevice(
                device_id=device_id,
                is_online=False,
            )

        return device_id

    def _increment_seq(self) -> int:
        """Increment and return message sequence number (rolls over at 256)."""
        current = self.msg_seq
        self.msg_seq = (self.msg_seq + 1) % 256
        return current

    def _quality_to_sparkplug(self, quality: PLCQualityCode) -> int:
        """Convert PLC quality code to Sparkplug quality code (OPC UA format).

        Sparkplug B uses OPC UA quality codes:
        - 192 (0xC0) = Good
        - 64 (0x40) = Uncertain
        - 0 (0x00) = Bad
        """
        if quality in [PLCQualityCode.GOOD, PLCQualityCode.GOOD_LOCAL_OVERRIDE]:
            return 192  # Good
        elif quality == PLCQualityCode.UNCERTAIN:
            return 64  # Uncertain
        else:
            return 0  # Bad

    def _sensor_to_metric_name(self, sensor_name: str) -> str:
        """Convert sensor name to Sparkplug metric name.

        Example: crusher_1_motor_power -> Crusher/Motor/Power
        """
        parts = sensor_name.split("_")
        # Capitalize and join with /
        metric_parts = [part.capitalize() for part in parts if not part.isdigit()]
        return "/".join(metric_parts)

    def register_sensor(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        industry: str,
        sensor_type: str,
        unit: str,
    ):
        """Register a sensor as a Sparkplug B metric."""
        device_id = self._get_device_for_sensor(sensor_name, industry)
        device = self.devices[device_id]

        metric_name = self._sensor_to_metric_name(sensor_name)

        # Determine datatype based on sensor value
        datatype = SparkplugDataType.FLOAT  # Default for most sensor values

        # Store metric definition
        self.metric_definitions[sensor_name] = datatype

        # Add to device metrics (if not already present)
        if metric_name not in device.get_metric_names():
            device.metrics.append(
                SparkplugMetric(
                    name=metric_name,
                    datatype=datatype,
                    value=0.0,
                    timestamp=int(time.time() * 1000),
                    properties={
                        "EngUnit": unit,
                        "SensorType": sensor_type,
                    }
                )
            )

    def generate_nbirth(self) -> Dict[str, Any]:
        """Generate NBIRTH (Edge Node Birth) message."""
        self.bd_seq += 1
        self.msg_seq = 0
        self.edge_node_online = True
        self.edge_node_birth_time = time.time()

        timestamp_ms = int(time.time() * 1000)

        # NBIRTH contains edge node metrics
        nbirth = {
            "timestamp": timestamp_ms,
            "seq": self._increment_seq(),
            "metrics": [
                {
                    "name": "bdSeq",
                    "timestamp": timestamp_ms,
                    "dataType": "Int64",
                    "value": self.bd_seq,
                },
                {
                    "name": "Node Control/Rebirth",
                    "timestamp": timestamp_ms,
                    "dataType": "Boolean",
                    "value": False,
                }
            ]
        }

        logger.info(f"Generated NBIRTH: bdSeq={self.bd_seq}, seq={nbirth['seq']}")
        return nbirth

    def generate_dbirth(self, device_id: str) -> Dict[str, Any]:
        """Generate DBIRTH (Device Birth) message."""
        if device_id not in self.devices:
            raise ValueError(f"Unknown device: {device_id}")

        device = self.devices[device_id]
        device.is_online = True

        timestamp_ms = int(time.time() * 1000)

        # DBIRTH contains all metrics with their definitions
        metrics = []
        for metric in device.metrics:
            metrics.append({
                "name": metric.name,
                "timestamp": timestamp_ms,
                "dataType": metric.datatype.name,
                "value": metric.value,
                "properties": metric.properties,
            })

        dbirth = {
            "timestamp": timestamp_ms,
            "seq": self._increment_seq(),
            "metrics": metrics,
        }

        device.last_birth_seq = dbirth["seq"]
        logger.info(f"Generated DBIRTH for {device_id}: {len(metrics)} metrics, seq={dbirth['seq']}")
        return dbirth

    def _generate_ndeath(self) -> Dict[str, Any]:
        """Generate NDEATH (Edge Node Death) message."""
        timestamp_ms = int(time.time() * 1000)

        ndeath = {
            "timestamp": timestamp_ms,
            "metrics": [
                {
                    "name": "bdSeq",
                    "timestamp": timestamp_ms,
                    "dataType": "Int64",
                    "value": self.bd_seq,
                }
            ]
        }

        self.edge_node_online = False
        logger.info(f"Generated NDEATH: bdSeq={self.bd_seq}")
        return ndeath

    def format_sensor_data(
        self,
        sensor_name: str,
        value: float,
        quality: PLCQualityCode,
        timestamp: float,
        plc_instance: PLCSimulator,
        **metadata
    ) -> Dict[str, Any]:
        """Format sensor data as Sparkplug B DDATA message."""

        # Check if we should publish (Change of Value)
        if self._should_publish_cov(sensor_name, value):
            self.last_values[sensor_name] = value
        else:
            return None  # Skip publishing (no significant change)

        # Get device for this sensor
        industry = metadata.get("industry", "unknown")
        device_id = self._get_device_for_sensor(sensor_name, industry)

        # Register if not already registered
        if sensor_name not in self.metric_definitions:
            self.register_sensor(
                sensor_name,
                plc_instance,
                industry,
                metadata.get("sensor_type", "unknown"),
                metadata.get("unit", ""),
            )

        metric_name = self._sensor_to_metric_name(sensor_name)
        timestamp_ms = int(timestamp * 1000)
        quality_code = self._quality_to_sparkplug(quality)

        # DDATA format
        ddata = {
            "timestamp": timestamp_ms,
            "seq": self._increment_seq(),
            "metrics": [{
                "name": metric_name,
                "timestamp": timestamp_ms,
                "dataType": "Float",
                "value": value,
                "properties": {
                    "Quality": quality_code,
                    "EngUnit": metadata.get("unit", ""),
                }
            }]
        }

        # Update metrics
        payload_size = len(json.dumps(ddata).encode("utf-8"))
        self.metrics.update_message_sent(payload_size, quality)

        return ddata

    def _should_publish_cov(self, sensor_name: str, new_value: float) -> bool:
        """Check if value has changed significantly (Change of Value)."""
        if sensor_name not in self.last_values:
            return True  # Always publish first value

        last_value = self.last_values[sensor_name]
        if last_value == 0:
            return abs(new_value) > self.cov_threshold

        # Calculate percentage change
        pct_change = abs((new_value - last_value) / last_value)
        return pct_change > self.cov_threshold

    def get_opcua_node_id(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Sparkplug B is MQTT-only, but provide node ID for compatibility."""
        industry = metadata.get("industry", "unknown")
        device_id = self._get_device_for_sensor(sensor_name, industry)
        metric_name = self._sensor_to_metric_name(sensor_name)

        return f"ns=2;s=SparkplugB.{self.edge_node_id}.{device_id}.{metric_name}"

    def get_mqtt_topic(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Get Sparkplug B MQTT topic.

        Format: spBv1.0/{group_id}/DDATA/{edge_node_id}/{device_id}
        """
        industry = metadata.get("industry", "unknown")
        device_id = self._get_device_for_sensor(sensor_name, industry)

        return f"spBv1.0/{self.group_id}/DDATA/{self.edge_node_id}/{device_id}"

    def get_birth_topic(self, message_type: SparkplugMessageType, device_id: Optional[str] = None) -> str:
        """Get topic for BIRTH/DEATH messages."""
        if message_type in [SparkplugMessageType.NBIRTH, SparkplugMessageType.NDEATH]:
            return f"spBv1.0/{self.group_id}/{message_type.value}/{self.edge_node_id}"
        elif message_type in [SparkplugMessageType.DBIRTH, SparkplugMessageType.DDEATH]:
            if not device_id:
                raise ValueError("device_id required for DBIRTH/DDEATH")
            return f"spBv1.0/{self.group_id}/{message_type.value}/{self.edge_node_id}/{device_id}"
        else:
            raise ValueError(f"Unsupported message type: {message_type}")

    def get_nbirth_topic(self) -> str:
        """Get NBIRTH topic."""
        return f"spBv1.0/{self.group_id}/NBIRTH/{self.edge_node_id}"

    def get_dbirth_topic(self, device_id: str) -> str:
        """Get DBIRTH topic for a specific device."""
        return f"spBv1.0/{self.group_id}/DBIRTH/{self.edge_node_id}/{device_id}"

    def get_device_dbirths(self) -> Dict[str, Dict[str, Any]]:
        """Generate DBIRTH messages for all devices."""
        dbirths = {}
        for device_id in self.devices.keys():
            try:
                dbirth = self.generate_dbirth(device_id)
                dbirths[device_id] = dbirth
            except Exception as e:
                logger.error(f"Failed to generate DBIRTH for {device_id}: {e}")
        return dbirths

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get Sparkplug B diagnostics."""
        import datetime

        # Format birth time
        birth_time_str = None
        birth_time_ago = None
        if self.edge_node_birth_time:
            birth_dt = datetime.datetime.fromtimestamp(self.edge_node_birth_time)
            birth_time_str = birth_dt.strftime("%Y-%m-%d %H:%M:%S")
            seconds_ago = time.time() - self.edge_node_birth_time
            if seconds_ago < 60:
                birth_time_ago = f"{int(seconds_ago)}s ago"
            elif seconds_ago < 3600:
                birth_time_ago = f"{int(seconds_ago / 60)}m ago"
            else:
                hours = int(seconds_ago / 3600)
                minutes = int((seconds_ago % 3600) / 60)
                birth_time_ago = f"{hours}h {minutes}m ago"

        return {
            "group_id": self.group_id,
            "edge_node_id": self.edge_node_id,
            "bd_seq": self.bd_seq,
            "msg_seq": self.msg_seq,
            "edge_node_online": self.edge_node_online,
            "edge_node_state": "🟢 OPERATIONAL" if self.edge_node_online else "🔴 OFFLINE",
            "edge_node_birth_time": self.edge_node_birth_time,
            "edge_node_birth_time_formatted": birth_time_str,
            "edge_node_birth_time_ago": birth_time_ago,
            "devices": [
                {
                    "device_id": device_id,
                    "is_online": device.is_online,
                    "state": "🟢 Online" if device.is_online else "🔴 Offline",
                    "metric_count": len(device.metrics),
                    "last_birth_seq": device.last_birth_seq,
                }
                for device_id, device in self.devices.items()
            ],
            "use_protobuf": self.use_protobuf,
            "cov_threshold": self.cov_threshold,
        }
