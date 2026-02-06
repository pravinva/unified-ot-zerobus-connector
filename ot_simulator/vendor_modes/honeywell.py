"""Honeywell Experion mode - PKS/PlantCruise DCS composite points.

Honeywell Experion PKS (Process Knowledge System) uses composite points
where each measurement has multiple attributes:
- .PV (Process Value)
- .SP (Setpoint)
- .OP (Output)
- .PVEUHI (Engineering Units High)
- .PVEULO (Engineering Units Low)
- .PVUNITS (Engineering Units)
- .PVBAD (Bad quality indicator)
- .PVHIALM (High Alarm)
- .PVLOALM (Low Alarm)

Organized into modules:
- FIM (Field I/O Module) - Direct sensor connections
- ACE (Advanced Control Environment) - PID controllers
- LCN (Local Control Network) - SCADA points

Example OPC UA: ns=2;s=EXPERION_PKS.FIM_01.CRUSH_PRIM_MOTOR_CURRENT.PV
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ot_simulator.plc_models import PLCSimulator, PLCQualityCode
from ot_simulator.sensor_models import SensorConfig
from ot_simulator.vendor_modes.base import (
    ModeConfig,
    ModeStatus,
    VendorMode,
    VendorModeType,
)

logger = logging.getLogger("ot_simulator.honeywell")


class ExperionModuleType(str, Enum):
    """Honeywell Experion module types."""

    FIM = "FIM"  # Field I/O Module (analog/digital I/O)
    ACE = "ACE"  # Advanced Control Environment (controllers)
    LCN = "LCN"  # Local Control Network (SCADA points)
    UCN = "UCN"  # Universal Control Network (legacy)


class ControlMode(str, Enum):
    """Controller operating modes."""

    AUTO = "Auto"  # Automatic control
    MANUAL = "Manual"  # Manual control
    CASCADE = "Cascade"  # Cascaded from another controller
    IMAN = "IMan"  # Initialization Manual
    LO = "LO"  # Local Override


@dataclass
class CompositePoint:
    """Honeywell Experion composite point structure."""

    name: str  # e.g., "CRUSH_PRIM_MOTOR_CURRENT"
    module: str  # e.g., "FIM_01"
    sensor_name: str  # Original sensor name

    # Process Value attributes
    pv: float = 0.0  # Process Value
    pveuhi: float = 100.0  # Engineering Units High
    pveulo: float = 0.0  # Engineering Units Low
    pvunits: str = ""  # Engineering Units
    pvbad: bool = False  # Bad quality flag
    pvhialm: float = 90.0  # High alarm setpoint
    pvloalm: float = 10.0  # Low alarm setpoint

    # Status
    pv_quality: int = 192  # OPC UA quality code (192=Good)

    def get_attributes(self) -> Dict[str, Any]:
        """Get all attributes as dictionary."""
        return {
            "PV": self.pv,
            "PVEUHI": self.pveuhi,
            "PVEULO": self.pveulo,
            "PVUNITS": self.pvunits,
            "PVBAD": self.pvbad,
            "PVHIALM": self.pvhialm,
            "PVLOALM": self.pvloalm,
        }


@dataclass
class ControllerPoint(CompositePoint):
    """Experion controller (ACE) with PID functionality."""

    # Setpoint attributes
    sp: float = 50.0  # Setpoint
    speuhi: float = 100.0
    speulo: float = 0.0

    # Output attributes
    op: float = 50.0  # Output (0-100%)
    opeuhi: float = 100.0
    opeulo: float = 0.0

    # Control mode
    mode: ControlMode = ControlMode.AUTO

    # PID tuning
    gain: float = 0.5
    reset: float = 5.0  # Integral time (minutes)
    rate: float = 0.5  # Derivative time (minutes)

    def get_attributes(self) -> Dict[str, Any]:
        """Get all attributes including controller-specific ones."""
        attrs = super().get_attributes()
        attrs.update({
            "SP": self.sp,
            "SPEUHI": self.speuhi,
            "SPEULO": self.speulo,
            "OP": self.op,
            "OPEUHI": self.opeuhi,
            "OPEULO": self.opeulo,
            "MODE": self.mode.value,
            "GAIN": self.gain,
            "RESET": self.reset,
            "RATE": self.rate,
        })
        return attrs


@dataclass
class ExperionModule:
    """Honeywell Experion module (FIM/ACE/LCN)."""

    name: str
    module_type: ExperionModuleType
    points: List[CompositePoint] = field(default_factory=list)

    def get_point_count(self) -> int:
        """Get number of points in this module."""
        return len(self.points)

    def get_node_count(self) -> int:
        """Get total OPC UA node count (point + attributes)."""
        total = 0
        for point in self.points:
            if isinstance(point, ControllerPoint):
                total += 16  # More attributes for controllers
            else:
                total += 7  # Standard composite point attributes
        return total


class HoneywellMode(VendorMode):
    """Honeywell Experion PKS mode implementation."""

    def __init__(self, config: ModeConfig):
        super().__init__(config)

        # Honeywell-specific configuration
        self.server_name = config.settings.get("server_name", "MINE_A_EXPERION_PKS")
        self.pks_version = config.settings.get("pks_version", "R520")

        # Module organization
        self.modules: Dict[str, ExperionModule] = {}

        # Point lookup
        self.sensor_to_point: Dict[str, str] = {}  # sensor_name -> point_name

    async def initialize(self) -> bool:
        """Initialize Honeywell Experion mode."""
        try:
            logger.info(f"Initializing Honeywell Experion mode: {self.server_name}")

            # Load module configuration
            module_config = self.config.settings.get("modules", {})
            if not module_config:
                logger.warning("No module configuration, creating defaults")
                self._create_default_modules()
            else:
                self._load_modules(module_config)

            self.metrics.status = ModeStatus.ACTIVE
            logger.info(
                f"Honeywell Experion mode initialized: {len(self.modules)} modules, "
                f"{sum(m.get_point_count() for m in self.modules.values())} points"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Honeywell mode: {e}", exc_info=True)
            self.metrics.status = ModeStatus.ERROR
            self.metrics.update_error(str(e))
            return False

    async def shutdown(self):
        """Shutdown Honeywell Experion mode."""
        logger.info("Shutting down Honeywell Experion mode...")
        self.metrics.status = ModeStatus.DISABLED

    def _create_default_modules(self):
        """Create default module structure."""
        # FIM module for field I/O
        fim_module = ExperionModule(
            name="FIM_01",
            module_type=ExperionModuleType.FIM,
        )
        self.modules["FIM_01"] = fim_module

        # ACE module for controllers
        ace_module = ExperionModule(
            name="ACE_01",
            module_type=ExperionModuleType.ACE,
        )
        self.modules["ACE_01"] = ace_module

        # LCN module for SCADA points
        lcn_module = ExperionModule(
            name="LCN_01",
            module_type=ExperionModuleType.LCN,
        )
        self.modules["LCN_01"] = lcn_module

    def _load_modules(self, module_config: Dict[str, Any]):
        """Load module configuration."""
        for module_name, module_cfg in module_config.items():
            module_type = ExperionModuleType(module_cfg.get("type", "FIM"))
            module = ExperionModule(
                name=module_name,
                module_type=module_type,
            )
            self.modules[module_name] = module

    def _sensor_to_point_name(self, sensor_name: str) -> str:
        """Convert sensor name to Experion point name.

        Example: crusher_1_motor_power -> CRUSH_01_MOTOR_POWER
        """
        # Convert to uppercase and keep underscores
        point_name = sensor_name.upper()

        # Abbreviate common terms
        abbreviations = {
            "CRUSHER": "CRUSH",
            "CONVEYOR": "CONV",
            "TEMPERATURE": "TEMP",
            "PRESSURE": "PRES",
            "VIBRATION": "VIB",
            "BEARING": "BRG",
        }

        for full, abbrev in abbreviations.items():
            point_name = point_name.replace(full, abbrev)

        return point_name

    def _get_module_for_sensor(
        self,
        sensor_name: str,
        sensor_type: str,
        is_controller: bool = False
    ) -> str:
        """Determine which module a sensor belongs to."""
        if is_controller:
            # Controllers go to ACE module
            return "ACE_01"
        elif "flow" in sensor_type.lower() or "level" in sensor_type.lower():
            # Process measurements that might need control
            return "ACE_01"
        elif any(term in sensor_name for term in ["status", "alarm", "count"]):
            # Discrete/status points go to LCN
            return "LCN_01"
        else:
            # Analog I/O goes to FIM
            return "FIM_01"

    def register_sensor(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        sensor_config: SensorConfig,
    ):
        """Register a sensor as an Experion composite point."""
        point_name = self._sensor_to_point_name(sensor_name)

        # Determine module
        is_controller = sensor_config.sensor_type.value in ["flow", "level", "temperature"]
        module_name = self._get_module_for_sensor(
            sensor_name,
            sensor_config.sensor_type.value,
            is_controller
        )

        if module_name not in self.modules:
            self._create_default_modules()

        module = self.modules[module_name]

        # Check if already registered
        if any(p.name == point_name for p in module.points):
            return

        # Create composite point or controller
        if module.module_type == ExperionModuleType.ACE and is_controller:
            point = ControllerPoint(
                name=point_name,
                module=module_name,
                sensor_name=sensor_name,
                pveuhi=sensor_config.max_value,
                pveulo=sensor_config.min_value,
                pvunits=sensor_config.unit,
                sp=sensor_config.nominal_value,
                pvhialm=sensor_config.max_value * 0.9,
                pvloalm=sensor_config.min_value * 1.1,
            )
        else:
            point = CompositePoint(
                name=point_name,
                module=module_name,
                sensor_name=sensor_name,
                pveuhi=sensor_config.max_value,
                pveulo=sensor_config.min_value,
                pvunits=sensor_config.unit,
                pvhialm=sensor_config.max_value * 0.9,
                pvloalm=sensor_config.min_value * 1.1,
            )

        module.points.append(point)
        self.sensor_to_point[sensor_name] = point_name

    def _get_point(self, sensor_name: str) -> Optional[CompositePoint]:
        """Get composite point for a sensor."""
        if sensor_name not in self.sensor_to_point:
            return None

        point_name = self.sensor_to_point[sensor_name]

        # Find point in modules
        for module in self.modules.values():
            for point in module.points:
                if point.name == point_name:
                    return point

        return None

    def format_sensor_data(
        self,
        sensor_name: str,
        value: float,
        quality: PLCQualityCode,
        timestamp: float,
        plc_instance: PLCSimulator,
        **metadata
    ) -> Dict[str, Any]:
        """Format sensor data in Experion format.

        Returns all composite point attributes.
        """
        point = self._get_point(sensor_name)
        if not point:
            # Auto-register if configuration available
            sensor_config = metadata.get("sensor_config")
            if sensor_config:
                self.register_sensor(sensor_name, plc_instance, sensor_config)
                point = self._get_point(sensor_name)

        if not point:
            logger.warning(f"Point not found for sensor: {sensor_name}")
            return {}

        # Update point value
        point.pv = value
        point.pvbad = quality not in [PLCQualityCode.GOOD, PLCQualityCode.GOOD_LOCAL_OVERRIDE]

        # Convert quality to OPC UA code
        if quality in [PLCQualityCode.GOOD, PLCQualityCode.GOOD_LOCAL_OVERRIDE]:
            point.pv_quality = 192  # Good
        elif quality == PLCQualityCode.UNCERTAIN:
            point.pv_quality = 64  # Uncertain
        else:
            point.pv_quality = 0  # Bad

        # If it's a controller, update SP and OP
        if isinstance(point, ControllerPoint):
            # Simple PID simulation
            error = point.sp - point.pv
            point.op = 50.0 + (error * point.gain)  # Simplified P-only
            point.op = max(point.opeulo, min(point.opeuhi, point.op))

        # Format as composite structure
        timestamp_ms = int(timestamp * 1000)

        formatted = {
            "server": self.server_name,
            "module": point.module,
            "point": point.name,
            "timestamp": timestamp_ms,
            "attributes": point.get_attributes(),
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
        """Get OPC UA node ID for composite point.

        Returns the .PV attribute node ID.
        Example: ns=2;s=EXPERION_PKS.FIM_01.CRUSH_PRIM_MOTOR_CURRENT.PV
        """
        point = self._get_point(sensor_name)
        if not point:
            point_name = self._sensor_to_point_name(sensor_name)
            module_name = "FIM_01"  # Default
        else:
            point_name = point.name
            module_name = point.module

        return f"ns=2;s={self.server_name}.{module_name}.{point_name}.PV"

    def get_mqtt_topic(
        self,
        sensor_name: str,
        plc_instance: PLCSimulator,
        **metadata
    ) -> str:
        """Get MQTT topic for Experion point.

        Format: honeywell/{server}/{module}/{point}/{attribute}
        """
        point = self._get_point(sensor_name)
        if not point:
            point_name = self._sensor_to_point_name(sensor_name)
            module_name = "FIM_01"
        else:
            point_name = point.name
            module_name = point.module

        prefix = self.config.mqtt_topic_prefix or "honeywell"
        return f"{prefix}/{self.server_name}/{module_name}/{point_name}/PV"

    def get_all_node_ids(self, point_name: str, module_name: str) -> List[str]:
        """Get all OPC UA node IDs for a composite point (all attributes).

        Returns list of node IDs for PV, PVEUHI, PVEULO, etc.
        """
        module = self.modules.get(module_name)
        if not module:
            return []

        point = None
        for p in module.points:
            if p.name == point_name:
                point = p
                break

        if not point:
            return []

        node_ids = []
        for attr_name in point.get_attributes().keys():
            node_id = f"ns=2;s={self.server_name}.{module_name}.{point_name}.{attr_name}"
            node_ids.append(node_id)

        return node_ids

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get Honeywell Experion diagnostics."""
        module_stats = []
        for module in self.modules.values():
            module_stats.append({
                "name": module.name,
                "type": module.module_type.value,
                "point_count": module.get_point_count(),
                "node_count": module.get_node_count(),
                "controller_count": sum(
                    1 for p in module.points if isinstance(p, ControllerPoint)
                ),
            })

        total_points = sum(m.get_point_count() for m in self.modules.values())
        total_nodes = sum(m.get_node_count() for m in self.modules.values())

        return {
            "server_name": self.server_name,
            "pks_version": self.pks_version,
            "modules": module_stats,
            "total_modules": len(self.modules),
            "total_points": total_points,
            "total_nodes": total_nodes,
            "composite_structure": True,
        }
