"""MQTT Publisher Simulator with realistic industrial data.

Publishes sensor data to an MQTT broker using various payload formats.
Supports JSON, simple string, and Sparkplug B formats.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

try:
    import aiomqtt
except ImportError:
    aiomqtt = None  # type: ignore

try:
    from pysparkplug import Device, EdgeNode, DeviceMetric, DataType
except ImportError:
    Device = None  # type: ignore
    EdgeNode = None  # type: ignore
    DeviceMetric = None  # type: ignore
    DataType = None  # type: ignore

from ot_simulator.config_loader import MQTTConfig
from ot_simulator.sensor_models import IndustryType, SensorSimulator, get_industry_sensors
from ot_simulator.plc_models import PLCQualityCode

# Import vendor mode integration
try:
    from ot_simulator.vendor_modes.integration import VendorModeIntegration
    from ot_simulator.vendor_modes.base import VendorModeType
    VENDOR_MODES_AVAILABLE = True
except ImportError:
    VendorModeIntegration = None  # type: ignore
    VendorModeType = None  # type: ignore
    VENDOR_MODES_AVAILABLE = False

logger = logging.getLogger("ot_simulator.mqtt")


class MQTTSimulator:
    """MQTT publisher simulator with realistic sensor data."""

    def __init__(self, config: MQTTConfig, simulator_manager=None):
        if aiomqtt is None:
            raise ImportError("aiomqtt package required. Install with: pip install aiomqtt")

        self.config = config
        self.simulators: dict[str, SensorSimulator] = {}
        self.client: aiomqtt.Client | None = None
        self._running = False
        self._message_count = 0
        self._capture_counter = 0  # For sampling message capture
        self.simulator_manager = simulator_manager
        self.vendor_integration: VendorModeIntegration | None = None

    async def init(self):
        """Initialize MQTT client and sensors."""
        # Create simulators for enabled industries
        industry_types = []
        for industry_name in self.config.industries:
            try:
                industry_types.append(IndustryType(industry_name))
            except ValueError:
                logger.warning(f"Unknown industry type: {industry_name}")

        for industry in industry_types:
            sensors = get_industry_sensors(industry)
            for simulator in sensors:
                path = f"{industry.value}/{simulator.config.name}"
                self.simulators[path] = simulator

        logger.info(
            f"Initialized MQTT publisher with {len(self.simulators)} sensors across {len(industry_types)} industries"
        )

        # Initialize vendor mode integration if available
        if VENDOR_MODES_AVAILABLE and self.simulator_manager:
            try:
                # Reuse existing vendor_integration from simulator_manager if available
                if hasattr(self.simulator_manager, 'vendor_integration') and self.simulator_manager.vendor_integration:
                    self.vendor_integration = self.simulator_manager.vendor_integration
                    logger.info("✓ Using shared vendor mode integration for MQTT")
                else:
                    # Create new instance and store on simulator_manager for others to reuse
                    self.vendor_integration = VendorModeIntegration(self.simulator_manager)
                    await self.vendor_integration.initialize()
                    self.simulator_manager.vendor_integration = self.vendor_integration  # Share with other simulators
                    logger.info("✓ Vendor mode integration initialized for MQTT (shared instance created)")
            except Exception as e:
                logger.warning(f"Failed to initialize vendor modes: {e}")
                self.vendor_integration = None

    async def start(self):
        """Start publishing sensor data to MQTT broker.

        If broker connection fails, runs in headless mode where sensors are
        initialized but no publishing occurs. This allows Zero-Bus streaming
        to access sensor data without requiring an MQTT broker.
        """
        if not self.simulators:
            await self.init()

        # Connect to broker
        broker_host = self.config.broker.host
        broker_port = self.config.broker.tls_port if self.config.broker.use_tls else self.config.broker.port

        # Check if broker is running, if not try to start it
        if broker_host in ("localhost", "127.0.0.1"):
            await self._ensure_broker_running(broker_host, broker_port)

        tls_params = None
        if self.config.broker.use_tls:
            import ssl

            tls_params = aiomqtt.TLSParameters(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None,
            )

        self.client = aiomqtt.Client(
            hostname=broker_host,
            port=broker_port,
            username=self.config.auth.username or None,
            password=self.config.auth.password or None,
            identifier=self.config.client_id,
            clean_session=self.config.clean_session,
            keepalive=self.config.keepalive,
            tls_params=tls_params,
        )

        try:
            async with self.client:
                logger.info(f"MQTT client connected to {broker_host}:{broker_port}")
                self._running = True

                # Publish Sparkplug B BIRTH messages if vendor modes enabled
                if self.vendor_integration:
                    await self._publish_birth_messages()

                try:
                    # Calculate publish interval
                    publish_interval = 1.0 / self.config.publish_rate_hz

                    while self._running:
                        start_time = time.time()

                        if self.config.batch_publish:
                            # Publish all sensors at once
                            await self._publish_batch()
                        else:
                            # Publish sensors individually
                            for path, simulator in self.simulators.items():
                                await self._publish_sensor(path, simulator)

                        self._message_count += len(self.simulators)

                        # Log stats periodically
                        if self._message_count % 1000 == 0:
                            logger.info(f"Published {self._message_count} messages")

                        # Sleep for remaining time to maintain rate
                        elapsed = time.time() - start_time
                        sleep_time = max(0, publish_interval - elapsed)
                        if sleep_time > 0:
                            await asyncio.sleep(sleep_time)

                except asyncio.CancelledError:
                    logger.info("MQTT publisher stopping...")
                    self._running = False
                except Exception as e:
                    logger.exception(f"Error in MQTT publisher: {e}")
                    raise
        except Exception as broker_error:
            # Broker connection failed - run in headless mode
            logger.warning(f"MQTT broker connection failed: {broker_error}")
            logger.info("Running in headless mode - sensors active but not publishing to broker")
            logger.info("Zero-Bus streaming will still work by reading sensor data directly")
            self._running = True

            # Keep simulator running without broker connection
            try:
                while self._running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("MQTT simulator stopping...")
                self._running = False

    async def _ensure_broker_running(self, host: str, port: int):
        """Check if MQTT broker is running and start it if needed."""
        import socket

        # Check if broker is already running
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                logger.info(f"MQTT broker already running on {host}:{port}")
                return
        except Exception:
            pass

        # Start embedded Python MQTT broker (amqtt)
        try:
            from amqtt.broker import Broker

            logger.info(f"Starting embedded MQTT broker on 0.0.0.0:{port}...")

            # Create broker config
            broker_config = {
                'listeners': {
                    'default': {
                        'type': 'tcp',
                        'bind': f'0.0.0.0:{port}',
                    },
                },
                'auth': {
                    'allow-anonymous': True,
                },
                'topic-check': {
                    'enabled': False
                }
            }

            # Create and start broker in background
            self._broker = Broker(config=broker_config)
            asyncio.create_task(self._broker.start())

            # Wait a bit for broker to start
            await asyncio.sleep(2)
            logger.info(f"Embedded MQTT broker started successfully on 0.0.0.0:{port}")
            self._running = True  # Set running flag early
        except ImportError:
            logger.warning("amqtt package not available. Install with: pip install amqtt")
            logger.info("MQTT broker will not be started - clients can connect to external broker")
        except Exception as e:
            logger.warning(f"Failed to start embedded MQTT broker: {e}")
            logger.info("MQTT broker will not be started - clients can connect to external broker")

    async def _publish_sensor(self, path: str, simulator: SensorSimulator):
        """Publish a single sensor update.

        If vendor modes are enabled, publishes to all vendor-specific topics.
        Otherwise, uses legacy format.
        """
        if self.client is None:
            return

        # Update sensor value
        value = simulator.update()
        timestamp = time.time()

        # Split path into industry/sensor
        industry, sensor_name = path.split("/", 1)

        # If vendor modes are enabled, use multi-vendor publishing
        if self.vendor_integration:
            try:
                # Get PLC quality code (default to GOOD if not available)
                quality = PLCQualityCode.GOOD
                if self.simulator_manager and hasattr(self.simulator_manager, 'plc_manager'):
                    plc_mgr = self.simulator_manager.plc_manager
                    if plc_mgr:
                        # Get the PLC that controls this sensor
                        plc_instance = plc_mgr.get_plc_for_sensor(path)
                        if plc_instance:
                            # Read value with PLC behavior (quality, scan cycle, etc.)
                            plc_data = plc_instance.read_input(path)
                            quality = PLCQualityCode(plc_data.get('quality', 'Good'))

                # Format sensor data for all enabled vendor modes
                vendor_data = self.vendor_integration.format_sensor_data(
                    sensor_path=path,
                    value=value,
                    quality=quality,
                    timestamp=timestamp
                )

                # Debug log
                if not vendor_data:
                    logger.warning(f"No vendor data returned for {path}")
                else:
                    logger.info(f"Vendor data for {path}: {len(vendor_data)} modes")

                # Publish to each vendor mode's topic
                for mode_type, formatted_data in vendor_data.items():
                    if formatted_data:
                        # Get vendor-specific MQTT topic
                        topic = self.vendor_integration.get_mqtt_topic(
                            path,
                            mode_type
                        )

                        # Convert formatted data to payload
                        payload = json.dumps(formatted_data).encode("utf-8")

                        await self.client.publish(topic, payload=payload, qos=self.config.qos)
                        self._message_count += 1

                        # Capture message for live inspector (sample every 10th message to avoid flooding)
                        self._capture_counter += 1
                        if self._capture_counter % 10 == 0:
                            logger.info(f"Capturing message: mode={mode_type.value}, topic={topic}")
                            # Add sensor_path to payload if not already present
                            payload_with_path = formatted_data.copy() if isinstance(formatted_data, dict) else formatted_data
                            if isinstance(payload_with_path, dict) and 'sensor_path' not in payload_with_path:
                                payload_with_path['sensor_path'] = path

                            # Determine message type for Sparkplug B
                            msg_type = None
                            if mode_type == VendorModeType.SPARKPLUG_B:
                                msg_type = "DDATA"  # Regular data messages are DDATA

                            self.vendor_integration.capture_message(
                                mode_type=mode_type,
                                topic=topic,
                                payload=payload_with_path,
                                protocol="mqtt",
                                message_type=msg_type
                            )

                return  # Done with vendor mode publishing
            except Exception as e:
                logger.error(f"Error in vendor mode publishing for {path}: {e}, falling back to legacy")

        # Legacy publishing (fallback if vendor modes not available or error)
        # Create topic
        topic_base = f"{self.config.topic_prefix}/{industry}/{sensor_name}"

        # Create payload based on format
        if self.config.payload_format == "json":
            payload = self._create_json_payload(simulator, value)
            payload_bytes = json.dumps(payload).encode("utf-8")
        elif self.config.payload_format == "sparkplug_b":
            payload_bytes = self._create_sparkplug_payload(simulator, value)
        else:  # string
            payload_bytes = str(value).encode("utf-8")

        # Publish to value topic
        await self.client.publish(
            f"{topic_base}/value",
            payload_bytes,
            qos=self.config.qos,
            retain=False,
        )

        # Optionally publish metadata (once per sensor, not every update)
        if self.config.include_metadata and self._message_count < len(self.simulators):
            metadata = self._create_metadata(simulator)
            await self.client.publish(
                f"{topic_base}/metadata",
                json.dumps(metadata).encode("utf-8"),
                qos=1,
                retain=True,  # Retain metadata
            )

    async def _publish_batch(self):
        """Publish all sensors in a single batch message."""
        if self.client is None:
            return

        batch = {}
        timestamp = int(time.time() * 1000)

        for path, simulator in self.simulators.items():
            value = simulator.update()
            industry, sensor_name = path.split("/", 1)

            if industry not in batch:
                batch[industry] = {}

            batch[industry][sensor_name] = {
                "value": value,
                "unit": simulator.config.unit,
                "type": simulator.config.sensor_type.value,
                "timestamp": timestamp,
            }

        # Publish batch
        topic = f"{self.config.topic_prefix}/batch"
        payload = json.dumps(batch, indent=None).encode("utf-8")

        await self.client.publish(
            topic,
            payload,
            qos=self.config.qos,
            retain=False,
        )

    async def _publish_birth_messages(self):
        """Publish Sparkplug B BIRTH messages for all vendor modes that support it.

        This is called once when the MQTT client connects to announce all available sensors.
        """
        if not self.vendor_integration or not self.client:
            return

        try:
            # Get active modes
            active_modes = self.vendor_integration.mode_manager.get_active_modes()

            for mode in active_modes:
                mode_type = mode.config.mode_type

                # Check if this mode supports BIRTH messages (Sparkplug B)
                if mode_type == VendorModeType.SPARKPLUG_B:
                    try:
                        # Generate and publish NBIRTH (Node BIRTH)
                        nbirth = mode.generate_nbirth()
                        if nbirth:
                            nbirth_topic = mode.get_nbirth_topic()
                            nbirth_payload = json.dumps(nbirth).encode("utf-8")
                            await self.client.publish(nbirth_topic, nbirth_payload, qos=1)
                            logger.info(f"Published Sparkplug B NBIRTH to {nbirth_topic}")

                            # Capture NBIRTH message
                            if self.vendor_integration:
                                nbirth_with_meta = nbirth.copy()
                                nbirth_with_meta['message_type'] = 'NBIRTH'
                                self.vendor_integration.capture_message(
                                    mode_type=VendorModeType.SPARKPLUG_B,
                                    topic=nbirth_topic,
                                    payload=nbirth_with_meta,
                                    protocol="mqtt",
                                    message_type="NBIRTH"
                                )

                        # Generate and publish DBIRTH (Device BIRTH) for each device
                        # Register all sensors first
                        for sensor_path in self.simulators.keys():
                            # Get PLC if available for quality code
                            plc = None
                            if self.simulator_manager and hasattr(self.simulator_manager, 'plc_manager'):
                                plc_mgr = self.simulator_manager.plc_manager
                                if plc_mgr:
                                    for p in plc_mgr.plcs.values():
                                        if sensor_path in p.sensor_mappings:
                                            plc = p
                                            break

                            mode.register_sensor(sensor_path, plc_instance=plc)

                        # Get device DBIRTHs
                        dbirths = mode.get_device_dbirths()
                        for device_name, dbirth in dbirths.items():
                            dbirth_topic = mode.get_dbirth_topic(device_name)
                            dbirth_payload = json.dumps(dbirth).encode("utf-8")
                            await self.client.publish(dbirth_topic, dbirth_payload, qos=1)
                            logger.info(f"Published Sparkplug B DBIRTH for device {device_name}")

                            # Capture DBIRTH message
                            if self.vendor_integration:
                                dbirth_with_meta = dbirth.copy()
                                dbirth_with_meta['message_type'] = 'DBIRTH'
                                dbirth_with_meta['device_id'] = device_name
                                self.vendor_integration.capture_message(
                                    mode_type=VendorModeType.SPARKPLUG_B,
                                    topic=dbirth_topic,
                                    payload=dbirth_with_meta,
                                    protocol="mqtt",
                                    message_type="DBIRTH"
                                )

                    except Exception as e:
                        logger.error(f"Error publishing BIRTH messages for {mode_type}: {e}")

        except Exception as e:
            logger.error(f"Error in _publish_birth_messages: {e}")

    def _create_json_payload(self, simulator: SensorSimulator, value: float) -> dict[str, Any]:
        """Create JSON payload for sensor value."""
        payload: dict[str, Any] = {
            "value": round(value, 3),
            "unit": simulator.config.unit,
        }

        if self.config.include_timestamp:
            payload["timestamp"] = int(time.time() * 1000)

        if self.config.include_metadata:
            payload.update(
                {
                    "sensor_type": simulator.config.sensor_type.value,
                    "min": simulator.config.min_value,
                    "max": simulator.config.max_value,
                    "nominal": simulator.config.nominal_value,
                }
            )

        # Add fault status if active
        if simulator.fault_active:
            payload["fault"] = True
            payload["fault_end"] = int(simulator.fault_end_time * 1000)

        return payload

    def _create_sparkplug_payload(self, simulator: SensorSimulator, value: float) -> bytes:
        """Create proper Sparkplug B payload using protobuf encoding."""
        if Device is None:
            # Fallback to JSON if pysparkplug not available
            logger.warning("pysparkplug not available, using JSON fallback")
            payload = {
                "timestamp": int(time.time() * 1000),
                "metrics": [
                    {
                        "name": simulator.config.name,
                        "timestamp": int(time.time() * 1000),
                        "datatype": "Double",
                        "value": round(value, 3),
                        "properties": {
                            "unit": simulator.config.unit,
                            "type": simulator.config.sensor_type.value,
                        },
                    }
                ],
                "seq": self._message_count,
            }
            return json.dumps(payload).encode("utf-8")

        # Create proper Sparkplug B protobuf message
        try:
            from pysparkplug.protobuf.sparkplug_b import Payload

            payload = Payload()
            payload.timestamp = int(time.time() * 1000)
            payload.seq = self._message_count

            # Add metric
            metric = payload.metrics.add()
            metric.name = simulator.config.name
            metric.timestamp = int(time.time() * 1000)
            metric.datatype = DataType.Double.value
            metric.double_value = round(value, 3)

            # Add properties for unit and type
            prop_unit = metric.properties.add()
            prop_unit.key = "unit"
            prop_unit.value.string_value = simulator.config.unit
            prop_unit.value.type = DataType.String.value

            prop_type = metric.properties.add()
            prop_type.key = "sensor_type"
            prop_type.value.string_value = simulator.config.sensor_type.value
            prop_type.value.type = DataType.String.value

            # Add fault status if active
            if simulator.fault_active:
                prop_fault = metric.properties.add()
                prop_fault.key = "fault"
                prop_fault.value.boolean_value = True
                prop_fault.value.type = DataType.Boolean.value

            return payload.SerializeToString()
        except Exception as e:
            logger.error(f"Error creating Sparkplug B payload: {e}, falling back to JSON")
            # Fallback to JSON on error
            payload_dict = {
                "timestamp": int(time.time() * 1000),
                "metrics": [
                    {
                        "name": simulator.config.name,
                        "timestamp": int(time.time() * 1000),
                        "datatype": "Double",
                        "value": round(value, 3),
                        "properties": {
                            "unit": simulator.config.unit,
                            "type": simulator.config.sensor_type.value,
                        },
                    }
                ],
                "seq": self._message_count,
            }
            return json.dumps(payload_dict).encode("utf-8")

    def _create_metadata(self, simulator: SensorSimulator) -> dict[str, Any]:
        """Create metadata payload for sensor."""
        return {
            "name": simulator.config.name,
            "sensor_type": simulator.config.sensor_type.value,
            "unit": simulator.config.unit,
            "min_value": simulator.config.min_value,
            "max_value": simulator.config.max_value,
            "nominal_value": simulator.config.nominal_value,
            "update_frequency_hz": simulator.config.update_frequency_hz,
            "cyclic": simulator.config.cyclic,
        }

    async def stop(self):
        """Stop the MQTT publisher."""
        self._running = False

    def get_connected_subscribers(self) -> list[dict[str, Any]]:
        """Get list of MQTT subscribers (if broker provides this info).

        Note: This simulator is an MQTT publisher/client, not a broker.
        Tracking subscribers requires broker-side APIs which are not
        available through the standard MQTT client protocol.

        Returns:
            Empty list (subscriber tracking not available from client side)
        """
        # MQTT protocol doesn't provide subscriber information to publishers
        # This would require direct access to broker internals or broker-specific APIs
        # For example: Mosquitto has $SYS topics, HiveMQ has REST API, etc.

        return []

    def inject_fault(self, sensor_path: str, duration: float = 10.0):
        """Inject a fault into a specific sensor."""
        if sensor_path in self.simulators:
            self.simulators[sensor_path].inject_fault(duration)
            logger.info(f"Fault injected into {sensor_path} for {duration} seconds")
        else:
            logger.warning(f"Sensor {sensor_path} not found")

    def get_stats(self) -> dict[str, Any]:
        """Get publisher statistics."""
        return {
            "message_count": self._message_count,
            "sensor_count": len(self.simulators),
            "running": self._running,
            "broker": f"{self.config.broker.host}:{self.config.broker.port}",
            "qos": self.config.qos,
            "format": self.config.payload_format,
        }


async def run_mqtt_simulator(config: MQTTConfig):
    """Run MQTT simulator (convenience function)."""
    sim = MQTTSimulator(config)
    await sim.start()


if __name__ == "__main__":
    import sys
    from ot_simulator.config_loader import load_config

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Load config
    config_path = sys.argv[1] if len(sys.argv) > 1 else "ot_simulator/config.yaml"
    full_config = load_config(config_path)

    # Run MQTT simulator
    asyncio.run(run_mqtt_simulator(full_config.mqtt))
