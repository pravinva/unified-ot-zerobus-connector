"""Simulator Manager - coordinates all protocol simulators and sensor access."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from ot_simulator.sensor_models import IndustryType, get_industry_sensors

logger = logging.getLogger("ot_simulator.manager")


class SimulatorManager:
    """Manages all protocol simulators and provides unified sensor access."""

    def __init__(self):
        """Initialize simulator manager."""
        self.simulators: dict[str, Any] = {}
        self.sensor_instances: dict[str, Any] = {}  # sensor_path -> Sensor instance
        self.faults: dict[str, dict] = {}  # sensor_path -> {end_time, original_value, fault_type}
        self.plc_manager: Optional[Any] = None  # PLCManager instance (loaded lazily)
        self.replay_data: dict[str, list[dict]] = {}  # replay_id -> list of {timestamp, sensor_path, value}
        self.active_replays: dict[str, asyncio.Task] = {}  # replay_id -> task
        self._init_sensors()

    def _init_sensors(self):
        """Initialize all sensors from all industries."""
        for industry in IndustryType:
            sensors = get_industry_sensors(industry)
            for sensor in sensors:
                sensor_path = f"{industry.value}/{sensor.config.name}"
                self.sensor_instances[sensor_path] = sensor
                logger.debug(f"Registered sensor: {sensor_path}")

        logger.info(f"Initialized {len(self.sensor_instances)} sensors across {len(IndustryType)} industries")

    def init_plc_manager(self, config_path: Optional[str] = None):
        """Initialize PLC manager (optional).

        Args:
            config_path: Path to plc_config.yaml (defaults to ot_simulator/plc_config.yaml)
        """
        try:
            from ot_simulator.plc_manager import PLCManager

            self.plc_manager = PLCManager(self, config_path)
            if self.plc_manager.load_config():
                logger.info("✓ PLC Manager initialized")
            else:
                logger.info("PLC simulation disabled or config not found")
                self.plc_manager = None
        except Exception as e:
            logger.warning(f"Failed to initialize PLC manager: {e}")
            self.plc_manager = None

    def register_simulator(self, protocol: str, simulator: Any):
        """Register a protocol simulator.

        Args:
            protocol: Protocol name (opcua, mqtt, modbus)
            simulator: Simulator instance
        """
        self.simulators[protocol] = simulator
        logger.info(f"Registered {protocol.upper()} simulator")

    async def start_simulator(self, protocol: str):
        """Start a protocol simulator.

        Args:
            protocol: Protocol name (opcua, mqtt, modbus)
        """
        if protocol not in self.simulators:
            raise ValueError(f"Unknown protocol: {protocol}")

        simulator = self.simulators[protocol]
        if hasattr(simulator, "start"):
            await simulator.start()
        logger.info(f"Started {protocol.upper()} simulator")

    async def stop_simulator(self, protocol: str):
        """Stop a protocol simulator.

        Args:
            protocol: Protocol name (opcua, mqtt, modbus)
        """
        if protocol not in self.simulators:
            raise ValueError(f"Unknown protocol: {protocol}")

        simulator = self.simulators[protocol]
        if hasattr(simulator, "stop"):
            await simulator.stop()
        logger.info(f"Stopped {protocol.upper()} simulator")

    def get_sensor_value(self, sensor_path: str) -> float | None:
        """Get current value of a sensor.

        Args:
            sensor_path: Sensor path (e.g., "mining/crusher_1_motor_power")

        Returns:
            Current sensor value or None if sensor not found
        """
        sensor = self.sensor_instances.get(sensor_path)
        if sensor is None:
            return None

        # Get normal sensor value first
        normal_value = sensor.update()

        # Check if sensor has active fault
        if sensor_path in self.faults:
            fault_info = self.faults[sensor_path]
            current_time = asyncio.get_event_loop().time()

            if current_time < fault_info["end_time"]:
                # Apply fault transformation based on fault type
                fault_type = fault_info.get("fault_type", "fixed_value")
                params = fault_info.get("params", {})

                if fault_type == "fixed_value":
                    # Return fixed value
                    return params.get("value", normal_value)
                elif fault_type == "drift":
                    # Add drift offset
                    drift = params.get("drift", 0)
                    return normal_value + drift
                elif fault_type == "spike":
                    # Return spike value
                    return params.get("spike_value", normal_value * 2)
                elif fault_type == "noise":
                    # Add random noise
                    import random
                    noise_amplitude = params.get("amplitude", 5)
                    return normal_value + random.uniform(-noise_amplitude, noise_amplitude)
                elif fault_type == "stuck":
                    # Return stuck value (cached at fault start)
                    if "stuck_value" not in fault_info:
                        fault_info["stuck_value"] = normal_value
                    return fault_info["stuck_value"]
                else:
                    return normal_value
            else:
                # Fault expired, remove it
                del self.faults[sensor_path]

        # Return normal sensor value
        return normal_value

    def inject_fault(self, sensor_path: str, fault_type: str, params: dict[str, Any], duration: float = 0) -> bool:
        """Inject a fault into a sensor.

        Args:
            sensor_path: Sensor path (e.g., "mining/crusher_1_motor_power")
            fault_type: Type of fault ("fixed_value", "drift", "spike", "noise", "stuck")
            params: Fault parameters (e.g., {"value": 95.5} for fixed_value)
            duration: Fault duration in seconds (0 = permanent until cleared)

        Returns:
            True if successful, False if sensor not found
        """
        if sensor_path not in self.sensor_instances:
            logger.warning(f"Sensor not found: {sensor_path}")
            return False

        # Calculate fault end time
        end_time = asyncio.get_event_loop().time() + duration if duration > 0 else float('inf')

        # Store fault information
        self.faults[sensor_path] = {
            "end_time": end_time,
            "fault_type": fault_type,
            "params": params,
            "duration": duration,
        }

        logger.info(f"Injected {fault_type} fault into {sensor_path} for {duration}s")
        return True

    def get_all_sensor_paths(self) -> list[str]:
        """Get list of all available sensor paths."""
        return list(self.sensor_instances.keys())

    def get_sensors_by_industry(self, industry: str) -> list[dict]:
        """Get all sensors for a specific industry.

        Args:
            industry: Industry name (e.g., "mining")

        Returns:
            List of sensor info dictionaries
        """
        sensors = []
        prefix = f"{industry}/"

        for path, sensor in self.sensor_instances.items():
            if path.startswith(prefix):
                sensors.append(
                    {
                        "path": path,
                        "name": sensor.config.name,
                        "min_value": sensor.config.min_value,
                        "max_value": sensor.config.max_value,
                        "unit": sensor.config.unit,
                        "type": sensor.config.sensor_type.value,
                    }
                )

        return sensors

    def get_simulator_status(self) -> dict[str, Any]:
        """Get status of all simulators."""
        status = {}

        for protocol, simulator in self.simulators.items():
            status[protocol] = {
                "running": getattr(simulator, "running", False),
                "sensor_count": len(self.sensor_instances),
                "update_count": getattr(simulator, "update_count", 0),
                "errors": getattr(simulator, "error_count", 0),
            }

        return status

    # PLC-aware methods

    def get_sensor_value_with_plc(self, sensor_path: str) -> dict[str, Any]:
        """Get sensor value with PLC metadata (scan cycle, quality codes, etc.).

        This method routes the sensor read through the appropriate PLC if configured.

        Args:
            sensor_path: Sensor path (e.g., "mining/crusher_1_motor_power")

        Returns:
            Dictionary with value, quality, timestamp, PLC metadata
        """
        if self.plc_manager and self.plc_manager.enabled:
            return self.plc_manager.read_sensor_value(sensor_path)
        else:
            # No PLC simulation, read directly
            value = self.get_sensor_value(sensor_path)
            return {
                "value": value,
                "quality": "Good",
                "timestamp": asyncio.get_event_loop().time(),
                "plc_name": None,
                "plc_model": None,
                "forced": False,
            }

    def get_all_plcs(self) -> dict[str, dict[str, Any]]:
        """Get information about all configured PLCs."""
        if self.plc_manager and self.plc_manager.enabled:
            return self.plc_manager.get_all_plcs()
        return {}

    def get_plc_diagnostics(self, plc_name: Optional[str] = None) -> dict[str, Any]:
        """Get PLC diagnostics.

        Args:
            plc_name: Specific PLC name, or None for all PLCs

        Returns:
            Diagnostics dictionary
        """
        if not self.plc_manager or not self.plc_manager.enabled:
            return {}

        if plc_name:
            return self.plc_manager.get_plc_diagnostics(plc_name) or {}
        else:
            return self.plc_manager.get_all_diagnostics()

    def force_sensor_value(self, sensor_path: str, value: float) -> bool:
        """Force a sensor value through its PLC.

        Args:
            sensor_path: Sensor to force
            value: Forced value

        Returns:
            True if successful, False otherwise
        """
        if self.plc_manager and self.plc_manager.enabled:
            return self.plc_manager.force_value(sensor_path, value)
        return False

    def unforce_sensor_value(self, sensor_path: str) -> bool:
        """Remove forced value from sensor.

        Args:
            sensor_path: Sensor to unforce

        Returns:
            True if successful, False otherwise
        """
        if self.plc_manager and self.plc_manager.enabled:
            return self.plc_manager.unforce_value(sensor_path)
        return False

    # Training API support methods

    def set_replay_data(self, replay_id: str, rows: list[dict[str, Any]]):
        """Store CSV data for replay.

        Args:
            replay_id: Unique identifier for this replay
            rows: List of {timestamp, sensor_path, value} dictionaries
        """
        self.replay_data[replay_id] = rows
        logger.info(f"Stored replay data: {replay_id} with {len(rows)} rows")

    def start_replay(self, replay_id: str, speed: float = 1.0) -> bool:
        """Start replaying stored CSV data.

        Args:
            replay_id: Replay identifier
            speed: Playback speed multiplier (1.0 = real-time, 10.0 = 10x faster)

        Returns:
            True if replay started, False if replay_id not found
        """
        if replay_id not in self.replay_data:
            logger.warning(f"Replay ID not found: {replay_id}")
            return False

        # Cancel existing replay with same ID if running
        if replay_id in self.active_replays:
            self.active_replays[replay_id].cancel()

        # Start replay task
        task = asyncio.create_task(self._replay_task(replay_id, speed))
        self.active_replays[replay_id] = task
        logger.info(f"Started replay: {replay_id} at {speed}x speed")
        return True

    async def _replay_task(self, replay_id: str, speed: float):
        """Async task to replay CSV data.

        Args:
            replay_id: Replay identifier
            speed: Playback speed multiplier
        """
        try:
            rows = self.replay_data[replay_id]
            if not rows:
                logger.warning(f"No data to replay for {replay_id}")
                return

            logger.info(f"Replaying {len(rows)} rows at {speed}x speed")

            # Parse timestamps and sort by time
            import datetime
            for row in rows:
                if isinstance(row["timestamp"], str):
                    try:
                        # Try parsing ISO format
                        dt = datetime.datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                        row["timestamp"] = dt.timestamp()
                    except ValueError:
                        # If parsing fails, use current time
                        row["timestamp"] = asyncio.get_event_loop().time()

            sorted_rows = sorted(rows, key=lambda x: x["timestamp"])
            start_time = asyncio.get_event_loop().time()
            first_timestamp = sorted_rows[0]["timestamp"]

            # Replay each row at the correct time
            for row in sorted_rows:
                sensor_path = row["sensor_path"]
                value = row["value"]
                timestamp = row["timestamp"]

                # Calculate wait time based on speed multiplier
                time_offset = (timestamp - first_timestamp) / speed
                target_time = start_time + time_offset
                current_time = asyncio.get_event_loop().time()

                if current_time < target_time:
                    await asyncio.sleep(target_time - current_time)

                # Inject value as fixed fault with short duration
                self.inject_fault(
                    sensor_path=sensor_path,
                    fault_type="fixed_value",
                    params={"value": value},
                    duration=1.0 / speed  # Duration scales with speed
                )

            logger.info(f"Replay completed: {replay_id}")

        except asyncio.CancelledError:
            logger.info(f"Replay cancelled: {replay_id}")
        except Exception as e:
            logger.error(f"Error during replay {replay_id}: {e}")
        finally:
            # Clean up
            if replay_id in self.active_replays:
                del self.active_replays[replay_id]

    def stop_replay(self, replay_id: str) -> bool:
        """Stop an active replay.

        Args:
            replay_id: Replay identifier

        Returns:
            True if replay was stopped, False if not running
        """
        if replay_id not in self.active_replays:
            return False

        self.active_replays[replay_id].cancel()
        del self.active_replays[replay_id]
        logger.info(f"Stopped replay: {replay_id}")
        return True

    def get_active_replays(self) -> list[str]:
        """Get list of active replay IDs."""
        return list(self.active_replays.keys())

    def clear_fault(self, sensor_path: str) -> bool:
        """Clear fault from a sensor.

        Args:
            sensor_path: Sensor path

        Returns:
            True if fault was cleared, False if no fault present
        """
        if sensor_path in self.faults:
            del self.faults[sensor_path]
            logger.info(f"Cleared fault from {sensor_path}")
            return True
        return False

    def get_active_faults(self) -> dict[str, dict]:
        """Get all active faults.

        Returns:
            Dictionary of sensor_path -> fault_info
        """
        # Clean up expired faults
        current_time = asyncio.get_event_loop().time()
        expired = [path for path, fault in self.faults.items() if current_time >= fault["end_time"]]
        for path in expired:
            del self.faults[path]

        return dict(self.faults)
