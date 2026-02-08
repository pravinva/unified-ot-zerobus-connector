"""API routes for vendor mode management.

Provides REST endpoints for:
- Listing available vendor modes
- Getting mode status and diagnostics
- Enabling/disabling modes
- Viewing recent messages per mode
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from aiohttp import web

from ot_simulator.vendor_modes.base import VendorModeType
from ot_simulator.vendor_modes.integration import VendorModeIntegration

logger = logging.getLogger("ot_simulator.vendor_api")


class VendorModeAPIRoutes:
    """API routes for vendor mode management."""

    def __init__(self, vendor_integration: VendorModeIntegration):
        """Initialize API routes.

        Args:
            vendor_integration: VendorModeIntegration instance
        """
        self.vendor_integration = vendor_integration

    def setup_routes(self, app: web.Application):
        """Setup API routes on the web application.

        Args:
            app: aiohttp Application instance
        """
        # Vendor mode management endpoints
        app.router.add_get("/api/modes", self.handle_list_modes)
        app.router.add_get("/api/modes/{mode_type}", self.handle_get_mode)
        app.router.add_post("/api/modes/{mode_type}/toggle", self.handle_toggle_mode)
        app.router.add_post("/api/modes/{mode_type}/protocol/toggle", self.handle_toggle_protocol)
        app.router.add_get("/api/modes/{mode_type}/diagnostics", self.handle_get_diagnostics)
        app.router.add_get("/api/modes/{mode_type}/status", self.handle_get_mode_status)

        # Utility endpoints
        app.router.add_get("/api/modes/sensor/{sensor_path}/paths", self.handle_get_sensor_paths)
        app.router.add_get("/api/modes/messages/recent", self.handle_get_recent_messages)
        app.router.add_get("/api/modes/topics/active", self.handle_get_active_topics)
        app.router.add_get("/api/modes/metrics/comprehensive", self.handle_get_comprehensive_metrics)
        app.router.add_get("/api/connection/endpoints", self.handle_get_connection_endpoints)

        logger.info("Vendor mode API routes registered")

    async def handle_list_modes(self, request: web.Request) -> web.Response:
        """List all available vendor modes with their status.

        GET /api/modes

        Returns:
            {
                "modes": [
                    {
                        "mode_type": "kepware",
                        "display_name": "Kepware KEPServerEX",
                        "enabled": true,
                        "status": "active",
                        "description": "...",
                        "protocols": ["opcua", "mqtt"]
                    },
                    ...
                ]
            }
        """
        try:
            all_status = self.vendor_integration.get_all_mode_status()

            modes = []
            mode_info = {
                VendorModeType.GENERIC: {
                    "display_name": "Generic Mode",
                    "description": "Simple JSON/OPC UA format (default)",
                    "protocols": ["opcua", "mqtt"],
                },
                VendorModeType.KEPWARE: {
                    "display_name": "Kepware KEPServerEX",
                    "description": "Channel.Device.Tag structure with IoT Gateway format",
                    "protocols": ["opcua", "mqtt"],
                },
                VendorModeType.SPARKPLUG_B: {
                    "display_name": "Sparkplug B",
                    "description": "Eclipse IoT standard with BIRTH/DATA/DEATH lifecycle",
                    "protocols": ["mqtt"],
                },
                VendorModeType.HONEYWELL: {
                    "display_name": "Honeywell Experion PKS",
                    "description": "Composite points with .PV/.SP/.OP attributes",
                    "protocols": ["opcua", "mqtt"],
                },
            }

            for mode_type, status in all_status.items():
                config = status.get("config", {})
                metrics = status.get("metrics", {})

                mode_data = {
                    "mode_type": mode_type,
                    "enabled": config.get("enabled", False),
                    "status": metrics.get("status", "disabled"),
                    **mode_info.get(mode_type, {
                        "display_name": mode_type,
                        "description": "",
                        "protocols": [],
                    })
                }

                modes.append(mode_data)

            return web.json_response({
                "modes": modes,
                "total_modes": len(modes),
                "active_modes": sum(1 for m in modes if m["status"] == "active"),
            })

        except Exception as e:
            logger.error(f"Error listing modes: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_get_mode(self, request: web.Request) -> web.Response:
        """Get detailed information about a specific mode.

        GET /api/modes/{mode_type}

        Returns:
            {
                "mode_type": "kepware",
                "config": {...},
                "metrics": {...},
                "diagnostics": {...}
            }
        """
        try:
            mode_type_str = request.match_info["mode_type"]

            try:
                mode_type = VendorModeType(mode_type_str)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid mode type: {mode_type_str}"},
                    status=400
                )

            # Get status
            status = self.vendor_integration.get_mode_status(mode_type)

            # Get diagnostics if mode is active
            diagnostics = None
            if status.get("metrics", {}).get("status") == "active":
                try:
                    diagnostics = self.vendor_integration.get_mode_diagnostics(mode_type)
                except Exception as e:
                    logger.warning(f"Failed to get diagnostics for {mode_type}: {e}")
                    diagnostics = {"error": str(e)}

            return web.json_response({
                "mode_type": mode_type_str,
                **status,
                "diagnostics": diagnostics,
            })

        except Exception as e:
            logger.error(f"Error getting mode: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_toggle_mode(self, request: web.Request) -> web.Response:
        """Enable or disable a vendor mode.

        POST /api/modes/{mode_type}/toggle

        Body:
            {
                "enabled": true/false
            }

        Returns:
            {
                "mode_type": "kepware",
                "enabled": true,
                "status": "active",
                "message": "Mode enabled successfully"
            }
        """
        try:
            mode_type_str = request.match_info["mode_type"]

            try:
                mode_type = VendorModeType(mode_type_str)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid mode type: {mode_type_str}"},
                    status=400
                )

            # Parse request body
            try:
                data = await request.json()
            except json.JSONDecodeError:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400
                )

            enabled = data.get("enabled")
            if enabled is None:
                return web.json_response(
                    {"error": "Missing 'enabled' field in request body"},
                    status=400
                )

            # Enable or disable mode
            if enabled:
                success = await self.vendor_integration.enable_mode(mode_type)
                message = "Mode enabled successfully" if success else "Failed to enable mode"
            else:
                success = await self.vendor_integration.disable_mode(mode_type)
                message = "Mode disabled successfully" if success else "Failed to disable mode"

            if not success:
                return web.json_response(
                    {"error": message},
                    status=500
                )

            # Get updated status
            status = self.vendor_integration.get_mode_status(mode_type)

            return web.json_response({
                "mode_type": mode_type_str,
                "enabled": enabled,
                "status": status.get("metrics", {}).get("status"),
                "message": message,
            })

        except Exception as e:
            logger.error(f"Error toggling mode: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_toggle_protocol(self, request: web.Request) -> web.Response:
        """Toggle protocol (OPC UA or MQTT) for a specific vendor mode.

        POST /api/modes/{mode_type}/protocol/toggle

        Body:
            {
                "protocol": "opcua" or "mqtt",
                "enabled": true/false
            }

        Returns:
            {
                "mode_type": "kepware",
                "protocol": "opcua",
                "enabled": true,
                "message": "Protocol enabled successfully"
            }
        """
        try:
            mode_type_str = request.match_info["mode_type"]

            try:
                mode_type = VendorModeType(mode_type_str)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid mode type: {mode_type_str}"},
                    status=400
                )

            # Parse request body
            try:
                data = await request.json()
            except json.JSONDecodeError:
                return web.json_response(
                    {"error": "Invalid JSON body"},
                    status=400
                )

            protocol = data.get("protocol", "").lower()
            enabled = data.get("enabled")

            if protocol not in ["opcua", "mqtt"]:
                return web.json_response(
                    {"error": "protocol must be 'opcua' or 'mqtt'"},
                    status=400
                )

            if enabled is None:
                return web.json_response(
                    {"error": "Missing 'enabled' field in request body"},
                    status=400
                )

            # Get the mode
            mode = self.vendor_integration.mode_manager.get_mode(mode_type)
            if not mode:
                return web.json_response(
                    {"error": f"Mode {mode_type_str} not found"},
                    status=404
                )

            # Update protocol setting
            if protocol == "opcua":
                mode.config.opcua_enabled = enabled
            elif protocol == "mqtt":
                mode.config.mqtt_enabled = enabled

            # Update config file to persist the change
            await self._update_vendor_config(mode_type, protocol, enabled)

            message = f"{'Enabled' if enabled else 'Disabled'} {protocol.upper()} for {mode_type_str}"
            logger.info(message)

            return web.json_response({
                "mode_type": mode_type_str,
                "protocol": protocol,
                "enabled": enabled,
                "message": message,
            })

        except Exception as e:
            logger.error(f"Error toggling protocol: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def _update_vendor_config(self, mode_type: VendorModeType, protocol: str, enabled: bool):
        """Update vendor mode config file to persist protocol toggle."""
        import yaml
        from pathlib import Path

        config_path = Path(__file__).parent / "config.yaml"

        try:
            # Read current config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}

            # Update protocol setting
            mode_key = mode_type.value
            if mode_key not in config:
                config[mode_key] = {}

            if protocol == "opcua":
                config[mode_key]["opcua_enabled"] = enabled
            elif protocol == "mqtt":
                config[mode_key]["mqtt_enabled"] = enabled

            # Write back
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Updated {config_path}: {mode_key}.{protocol}_enabled = {enabled}")

        except Exception as e:
            logger.error(f"Failed to update vendor config: {e}")
            # Don't fail the request, just log the error

    async def handle_get_diagnostics(self, request: web.Request) -> web.Response:
        """Get diagnostics for a specific vendor mode.

        GET /api/modes/{mode_type}/diagnostics

        Returns mode-specific diagnostic information:
        - Kepware: channels, devices, tags, quality distribution
        - Sparkplug B: edge node, devices, sequences, lifecycle
        - Honeywell: modules, points, controllers, node count
        """
        try:
            mode_type_str = request.match_info["mode_type"]

            try:
                mode_type = VendorModeType(mode_type_str)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid mode type: {mode_type_str}"},
                    status=400
                )

            diagnostics = self.vendor_integration.get_mode_diagnostics(mode_type)

            return web.json_response({
                "mode_type": mode_type_str,
                "diagnostics": diagnostics,
            })

        except Exception as e:
            logger.error(f"Error getting diagnostics: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_get_mode_status(self, request: web.Request) -> web.Response:
        """Get status for a specific vendor mode.

        GET /api/modes/{mode_type}/status

        Returns:
            {
                "mode_type": "kepware",
                "enabled": true,
                "status": "active",
                "metrics": {
                    "messages_sent": 15360,
                    "messages_failed": 2,
                    "bytes_sent": 4792320,
                    "quality_distribution": {...},
                    "uptime_seconds": 11538,
                    "avg_message_rate": 758.2
                }
            }
        """
        try:
            mode_type_str = request.match_info["mode_type"]

            try:
                mode_type = VendorModeType(mode_type_str)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid mode type: {mode_type_str}"},
                    status=400
                )

            status = self.vendor_integration.get_mode_status(mode_type)

            return web.json_response({
                "mode_type": mode_type_str,
                **status,
            })

        except Exception as e:
            logger.error(f"Error getting mode status: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_get_sensor_paths(self, request: web.Request) -> web.Response:
        """Get vendor-specific paths (OPC UA node IDs and MQTT topics) for a sensor.

        GET /api/modes/sensor/{sensor_path}/paths

        Example: /api/modes/sensor/mining%2Fcrusher_1_motor_power/paths

        Returns:
            {
                "sensor_path": "mining/crusher_1_motor_power",
                "paths": {
                    "generic": {
                        "opcua_node_id": "ns=2;s=Industries/mining/crusher_1_motor_power",
                        "mqtt_topic": "sensors/mining/crusher_1_motor_power/value"
                    },
                    "kepware": {
                        "opcua_node_id": "ns=2;s=Siemens_S7_Crushing.Crusher_01.MotorPower",
                        "mqtt_topic": "kepware/Siemens_S7_Crushing/Crusher_01/MotorPower"
                    },
                    "sparkplug_b": {
                        "opcua_node_id": "...",
                        "mqtt_topic": "spBv1.0/DatabricksDemo/DDATA/OTSimulator01/MiningAssets"
                    }
                }
            }
        """
        try:
            sensor_path = request.match_info["sensor_path"]

            # Get paths for all enabled modes
            paths = {}

            for mode in self.vendor_integration.mode_manager.get_active_modes():
                mode_type = mode.config.mode_type

                try:
                    opcua_node = self.vendor_integration.get_opcua_node_id(
                        sensor_path,
                        mode_type
                    )
                    mqtt_topic = self.vendor_integration.get_mqtt_topic(
                        sensor_path,
                        mode_type
                    )

                    paths[mode_type.value] = {
                        "opcua_node_id": opcua_node,
                        "mqtt_topic": mqtt_topic,
                    }
                except Exception as e:
                    logger.warning(f"Failed to get paths for {mode_type}: {e}")
                    paths[mode_type.value] = {
                        "error": str(e)
                    }

            return web.json_response({
                "sensor_path": sensor_path,
                "paths": paths,
            })

        except Exception as e:
            logger.error(f"Error getting sensor paths: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_get_recent_messages(self, request: web.Request) -> web.Response:
        """Get recent vendor mode messages from the message buffer.

        GET /api/modes/messages/recent?limit=50&protocol=mqtt&mode=kepware&industry=mining

        Query Parameters:
            limit: Maximum number of messages to return (1-200, default 50)
            protocol: Filter by protocol (mqtt, opcua, modbus)
            mode: Filter by vendor mode (generic, kepware, sparkplug_b, honeywell)
            industry: Filter by industry (mining, utilities, manufacturing, oil_gas)

        Returns:
            {
                "messages": [
                    {
                        "timestamp": 1234567890.123,
                        "mode": "kepware",
                        "topic": "kepware/Channel1/Device1/MotorPower",
                        "payload": {...},
                        "protocol": "mqtt",
                        "industry": "mining"
                    },
                    ...
                ],
                "count": 50,
                "filters": {
                    "protocol": "mqtt",
                    "mode": "kepware",
                    "industry": "mining"
                }
            }
        """
        try:
            limit = int(request.query.get("limit", "50"))
            limit = max(1, min(200, limit))  # Clamp between 1 and 200

            # Get filter parameters
            protocol_filter = request.query.get("protocol", "").strip()
            mode_filter = request.query.get("mode", "").strip()
            industry_filter = request.query.get("industry", "").strip()

            # Get all recent messages
            all_messages = self.vendor_integration.get_recent_messages(limit * 2)  # Get more to account for filtering

            # Apply server-side filters
            filtered_messages = []
            for msg in all_messages:
                # Protocol filter
                if protocol_filter and msg.get("protocol") != protocol_filter:
                    continue

                # Mode filter
                if mode_filter and msg.get("mode") != mode_filter:
                    continue

                # Industry filter
                if industry_filter and msg.get("industry") != industry_filter:
                    continue

                filtered_messages.append(msg)

                # Stop once we have enough
                if len(filtered_messages) >= limit:
                    break

            return web.json_response({
                "messages": filtered_messages,
                "count": len(filtered_messages),
                "filters": {
                    "protocol": protocol_filter or None,
                    "mode": mode_filter or None,
                    "industry": industry_filter or None
                }
            })

        except Exception as e:
            logger.error(f"Error getting recent messages: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_get_active_topics(self, request: web.Request) -> web.Response:
        """Get list of active MQTT topics being published.

        GET /api/modes/topics/active

        Returns:
            {
                "topics": [
                    {
                        "topic": "kepware/Channel1/Device1/MotorPower",
                        "mode": "kepware",
                        "message_type": null,
                        "message_count": 1250,
                        "message_rate": 2.5,
                        "last_publish": 0.5
                    },
                    ...
                ],
                "total_topics": 125,
                "by_mode": {
                    "generic": 379,
                    "kepware": 379,
                    "sparkplug_b": 12
                }
            }
        """
        try:
            if not self.vendor_integration:
                return web.json_response(
                    {"error": "Vendor mode integration not available"},
                    status=503
                )

            topics_data = self.vendor_integration.get_active_topics()

            return web.json_response(topics_data)

        except Exception as e:
            logger.error(f"Error getting active topics: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_get_comprehensive_metrics(self, request: web.Request) -> web.Response:
        """Get comprehensive metrics for all vendor modes.

        GET /api/modes/metrics/comprehensive

        Returns:
            {
                "timestamp": 1234567890.123,
                "modes": {
                    "generic": {
                        "enabled": true,
                        "status": {...},
                        "diagnostics": {...}
                    },
                    ...
                },
                "aggregated": {
                    "total_messages": 45000,
                    "total_bytes": 12500000,
                    "active_modes": 2,
                    "message_rate": 758.5
                },
                "message_buffer_size": 100,
                "message_buffer_count": 87
            }
        """
        try:
            import time

            metrics = {
                "timestamp": time.time(),
                "modes": {},
                "aggregated": {
                    "total_messages": 0,
                    "total_bytes": 0,
                    "active_modes": 0,
                    "message_rate": 0.0,
                },
                "message_buffer_size": 100,
                "message_buffer_count": len(self.vendor_integration.message_buffer),
            }

            # Collect metrics from each mode
            for mode_type in VendorModeType:
                try:
                    status = self.vendor_integration.get_mode_status(mode_type)
                    diagnostics = self.vendor_integration.get_mode_diagnostics(mode_type)

                    metrics["modes"][mode_type.value] = {
                        "enabled": status.get("enabled", False),
                        "status": status,
                        "diagnostics": diagnostics,
                    }

                    # Aggregate metrics
                    if status.get("enabled"):
                        metrics["aggregated"]["active_modes"] += 1

                    mode_metrics = status.get("metrics", {})
                    metrics["aggregated"]["total_messages"] += mode_metrics.get("messages_sent", 0)
                    metrics["aggregated"]["total_bytes"] += mode_metrics.get("bytes_sent", 0)
                    metrics["aggregated"]["message_rate"] += mode_metrics.get("avg_message_rate", 0.0)

                except Exception as e:
                    logger.warning(f"Error getting metrics for {mode_type.value}: {e}")
                    metrics["modes"][mode_type.value] = {
                        "enabled": False,
                        "error": str(e)
                    }

            return web.json_response(metrics)

        except Exception as e:
            logger.error(f"Error getting comprehensive metrics: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_get_connection_endpoints(self, request: web.Request) -> web.Response:
        """Get all connection endpoints for protocols and vendor modes.

        GET /api/connection/endpoints

        Returns comprehensive connection information including:
        - Protocol endpoints (OPC-UA, MQTT, Modbus)
        - Vendor mode-specific topic patterns and node IDs
        - Example connection strings
        - Authentication requirements

        Returns:
            {
                "protocols": {
                    "opcua": {
                        "endpoint": "opc.tcp://localhost:4840/ot-simulator/server/",
                        "namespace": "http://databricks.com/iot-simulator",
                        "security": "NoSecurity",
                        "description": "OPC UA server with vendor-specific node hierarchies"
                    },
                    "mqtt": {
                        "broker": "localhost",
                        "port": 1883,
                        "tls": false,
                        "description": "MQTT broker for streaming sensor data"
                    },
                    "modbus": {
                        "host": "localhost",
                        "port": 5020,
                        "protocol": "TCP",
                        "description": "Modbus TCP server for industrial protocols"
                    }
                },
                "vendor_modes": {
                    "generic": {
                        "opcua_pattern": "ns=2;s=Industries/{industry}/{sensor}",
                        "mqtt_pattern": "sensors/{industry}/{sensor}/value",
                        "description": "Simple JSON/OPC UA format (default)",
                        "example_opcua": "ns=2;s=Industries/mining/crusher_1_motor_power",
                        "example_mqtt": "sensors/mining/crusher_1_motor_power/value"
                    },
                    "kepware": {
                        "opcua_pattern": "ns=2;s={channel}.{device}.{tag}",
                        "mqtt_pattern": "kepware/{channel}/{device}/{tag}",
                        "description": "Channel.Device.Tag structure with IoT Gateway format",
                        "example_opcua": "ns=2;s=Siemens_S7_Crushing.Crusher_01.MotorPower",
                        "example_mqtt": "kepware/Siemens_S7_Crushing/Crusher_01/MotorPower"
                    },
                    "sparkplug_b": {
                        "opcua_pattern": "ns=2;s=SparkplugB/{edge_node}/{device}",
                        "mqtt_pattern": "spBv1.0/{group_id}/{message_type}/{edge_node}/{device}",
                        "description": "Eclipse IoT standard with BIRTH/DATA/DEATH lifecycle",
                        "example_opcua": "ns=2;s=SparkplugB/OTSimulator01/MiningAssets",
                        "example_mqtt": "spBv1.0/DatabricksDemo/DDATA/OTSimulator01/MiningAssets"
                    },
                    "honeywell": {
                        "opcua_pattern": "ns=2;s={controller}/{module}/{point}.{attribute}",
                        "mqtt_pattern": "honeywell/{controller}/{module}/{point}/{attribute}",
                        "description": "Composite points with .PV/.SP/.OP attributes",
                        "example_opcua": "ns=2;s=PKS_C300/AIN101/CRUSHER_POWER.PV",
                        "example_mqtt": "honeywell/PKS_C300/AIN101/CRUSHER_POWER/PV"
                    }
                },
                "api_endpoints": {
                    "base_url": f"http://localhost:{request.app['config'].web_ui.port if 'config' in request.app else 8989}",
                    "rest_api": {
                        "sensors": "/api/sensors",
                        "industries": "/api/industries",
                        "modes": "/api/modes",
                        "diagnostics": "/api/modes/{mode}/diagnostics",
                        "metrics": "/api/modes/metrics/comprehensive"
                    },
                    "websocket": f"ws://localhost:{request.app['config'].web_ui.port if 'config' in request.app else 8989}/ws"
                },
                "plc_controllers": {
                    "description": "8 PLCs across 7 vendors with hierarchical tag structures",
                    "vendors": [
                        {"name": "Siemens S7-1500", "channels": ["Siemens_S7_Crushing", "Siemens_S7_Conveyor"]},
                        {"name": "Rockwell ControlLogix", "channels": ["AB_CLX_Grinding"]},
                        {"name": "ABB AC500", "channels": ["ABB_AC500_Utilities"]},
                        {"name": "Mitsubishi iQ-R", "channels": ["Mitsubishi_iQR_Manufacturing"]},
                        {"name": "Schneider M580", "channels": ["Schneider_M580_Process"]},
                        {"name": "Omron NJ/NX", "channels": ["Omron_NJ_Packaging"]},
                        {"name": "GE PACSystems RX3i", "channels": ["GE_RX3i_OilGas"]}
                    ]
                },
                "connection_examples": {
                    "opcua_python": {
                        "description": "Connect using asyncua Python library",
                        "code": "from asyncua import Client\\n\\nasync with Client('opc.tcp://localhost:4840/ot-simulator/server/') as client:\\n    # Generic mode\\n    node = client.get_node('ns=2;s=Industries/mining/crusher_1_motor_power')\\n    value = await node.read_value()"
                    },
                    "mqtt_python": {
                        "description": "Connect using paho-mqtt Python library",
                        "code": "import paho.mqtt.client as mqtt\\n\\nclient = mqtt.Client()\\nclient.connect('localhost', 1883)\\nclient.subscribe('sensors/+/+/value')  # Generic mode\\nclient.loop_start()"
                    },
                    "modbus_python": {
                        "description": "Connect using pymodbus library",
                        "code": "from pymodbus.client import ModbusTcpClient\\n\\nclient = ModbusTcpClient('localhost', port=5020)\\nclient.connect()\\nresult = client.read_holding_registers(0, 10, slave=1)"
                    }
                }
            }
        """
        try:
            # Get config from request app
            config = request.app.get('config')
            web_port = config.web_ui.port if config else 8989
            opcua_endpoint = config.opcua.endpoint if config else "opc.tcp://0.0.0.0:4840/ot-simulator/server/"
            mqtt_host = config.mqtt.broker.host if config else "localhost"
            mqtt_port = config.mqtt.broker.port if config else 1883
            mqtt_tls = config.mqtt.broker.use_tls if config else False
            modbus_host = config.modbus.tcp.host if config else "0.0.0.0"
            modbus_port = config.modbus.tcp.port if config else 5020

            # Build comprehensive endpoint documentation
            endpoints = {
                "protocols": {
                    "opcua": {
                        "endpoint": opcua_endpoint.replace("0.0.0.0", "localhost"),
                        "namespace": "http://databricks.com/iot-simulator",
                        "namespace_index": 2,
                        "security": "NoSecurity",
                        "description": "OPC UA server with vendor-specific node hierarchies",
                        "protocols_supported": ["generic", "kepware", "sparkplug_b", "honeywell"],
                        "vendor_endpoints": {
                            "generic": {
                                "endpoint": opcua_endpoint.replace("0.0.0.0", "localhost"),
                                "port": 4840,
                                "node_count": 379,
                                "description": "Default generic OPC UA nodes"
                            },
                            "kepware": {
                                "endpoint": opcua_endpoint.replace("0.0.0.0", "localhost").replace(":4840", ":49320"),
                                "port": 49320,
                                "node_count": 379,
                                "description": "Kepware KEPServerEX canonical port (simulated)",
                                "note": "Currently accessible via main endpoint at :4840 with Kepware node structure"
                            },
                            "honeywell": {
                                "endpoint": opcua_endpoint.replace("0.0.0.0", "localhost").replace(":4840", ":4897"),
                                "port": 4897,
                                "node_count": 1137,
                                "description": "Honeywell Experion PKS canonical port (simulated)",
                                "note": "Currently accessible via main endpoint at :4840 with Honeywell node structure"
                            }
                        }
                    },
                    "mqtt": {
                        "broker": mqtt_host if mqtt_host != "0.0.0.0" else "localhost",
                        "port": mqtt_port,
                        "tls": mqtt_tls,
                        "auth_required": False,
                        "description": "MQTT broker for streaming sensor data",
                        "protocols_supported": ["generic", "kepware", "sparkplug_b", "honeywell"]
                    },
                    "modbus": {
                        "host": modbus_host if modbus_host != "0.0.0.0" else "localhost",
                        "port": modbus_port,
                        "protocol": "TCP",
                        "slave_id": 1,
                        "description": "Modbus TCP server for industrial protocols",
                        "protocols_supported": ["generic"]
                    },
                    "websocket": {
                        "url": f"ws://localhost:{web_port}/ws",
                        "description": "WebSocket for real-time updates and metrics",
                        "update_frequency": "500ms"
                    }
                },
                "vendor_modes": {
                    "generic": {
                        "display_name": "Generic Mode",
                        "opcua_pattern": "ns=2;s=Industries/{industry}/{sensor}",
                        "mqtt_pattern": "sensors/{industry}/{sensor}/value",
                        "description": "Simple JSON/OPC UA format (default)",
                        "example_opcua": "ns=2;s=Industries/mining/crusher_1_motor_power",
                        "example_mqtt": "sensors/mining/crusher_1_motor_power/value",
                        "supported_protocols": ["opcua", "mqtt"]
                    },
                    "kepware": {
                        "display_name": "Kepware KEPServerEX",
                        "opcua_pattern": "ns=2;s={channel}.{device}.{tag}",
                        "mqtt_pattern": "kepware/{channel}/{device}/{tag}",
                        "description": "Channel.Device.Tag structure with IoT Gateway format",
                        "example_opcua": "ns=2;s=Siemens_S7_Crushing.Crusher_01.MotorPower",
                        "example_mqtt": "kepware/Siemens_S7_Crushing/Crusher_01/MotorPower",
                        "supported_protocols": ["opcua", "mqtt"]
                    },
                    "sparkplug_b": {
                        "display_name": "Sparkplug B",
                        "opcua_pattern": "ns=2;s=SparkplugB/{edge_node}/{device}",
                        "mqtt_pattern": "spBv1.0/{group_id}/{message_type}/{edge_node}/{device}",
                        "message_types": ["NBIRTH", "DBIRTH", "NDATA", "DDATA", "NDEATH", "DDEATH"],
                        "description": "Eclipse IoT standard with BIRTH/DATA/DEATH lifecycle",
                        "example_opcua": "ns=2;s=SparkplugB/OTSimulator01/MiningAssets",
                        "example_mqtt": "spBv1.0/DatabricksDemo/DDATA/OTSimulator01/MiningAssets",
                        "group_id": "DatabricksDemo",
                        "edge_node": "OTSimulator01",
                        "supported_protocols": ["mqtt"]
                    },
                    "honeywell": {
                        "display_name": "Honeywell Experion PKS",
                        "opcua_pattern": "ns=2;s={controller}/{module}/{point}.{attribute}",
                        "mqtt_pattern": "honeywell/{controller}/{module}/{point}/{attribute}",
                        "attributes": ["PV", "SP", "OP", "MODE"],
                        "description": "Composite points with .PV/.SP/.OP attributes",
                        "example_opcua": "ns=2;s=PKS_C300/AIN101/CRUSHER_POWER.PV",
                        "example_mqtt": "honeywell/PKS_C300/AIN101/CRUSHER_POWER/PV",
                        "supported_protocols": ["opcua", "mqtt"]
                    }
                },
                "api_endpoints": {
                    "base_url": f"http://localhost:{web_port}",
                    "rest_api": {
                        "sensors": "/api/sensors",
                        "industries": "/api/industries",
                        "modes": "/api/modes",
                        "mode_status": "/api/modes/{mode}/status",
                        "diagnostics": "/api/modes/{mode}/diagnostics",
                        "toggle_mode": "/api/modes/{mode}/toggle",
                        "sensor_paths": "/api/modes/sensor/{sensor_path}/paths",
                        "recent_messages": "/api/modes/messages/recent",
                        "metrics": "/api/modes/metrics/comprehensive",
                        "connection_info": "/api/connection/endpoints"
                    },
                    "websocket": f"ws://localhost:{web_port}/ws"
                },
                "plc_controllers": {
                    "description": "8 PLCs across 7 vendors with hierarchical tag structures",
                    "total_plcs": 8,
                    "total_vendors": 7,
                    "vendors": [
                        {"name": "Siemens S7-1500", "plc_count": 2, "channels": ["Siemens_S7_Crushing", "Siemens_S7_Conveyor"]},
                        {"name": "Rockwell ControlLogix", "plc_count": 1, "channels": ["AB_CLX_Grinding"]},
                        {"name": "ABB AC500", "plc_count": 1, "channels": ["ABB_AC500_Utilities"]},
                        {"name": "Mitsubishi iQ-R", "plc_count": 1, "channels": ["Mitsubishi_iQR_Manufacturing"]},
                        {"name": "Schneider M580", "plc_count": 1, "channels": ["Schneider_M580_Process"]},
                        {"name": "Omron NJ/NX", "plc_count": 1, "channels": ["Omron_NJ_Packaging"]},
                        {"name": "GE PACSystems RX3i", "plc_count": 1, "channels": ["GE_RX3i_OilGas"]}
                    ]
                },
                "data_coverage": {
                    "total_sensors": 379,
                    "total_industries": 16,
                    "industries": [
                        "mining", "utilities", "manufacturing", "oil_gas", "water_treatment",
                        "food_beverage", "pharmaceuticals", "automotive", "chemical", "pulp_paper",
                        "metals", "cement", "glass", "textiles", "renewable_energy", "smart_buildings"
                    ]
                },
                "connection_examples": {
                    "opcua_python": {
                        "description": "Connect using asyncua Python library",
                        "library": "asyncua",
                        "install": "pip install asyncua",
                        "code": f"from asyncua import Client\n\nasync with Client('{opcua_endpoint.replace('0.0.0.0', 'localhost')}') as client:\n    # Generic mode\n    node = client.get_node('ns=2;s=Industries/mining/crusher_1_motor_power')\n    value = await node.read_value()\n    print(f'Power: {{value}}')"
                    },
                    "mqtt_python": {
                        "description": "Connect using paho-mqtt Python library",
                        "library": "paho-mqtt",
                        "install": "pip install paho-mqtt",
                        "code": f"import paho.mqtt.client as mqtt\n\ndef on_message(client, userdata, msg):\n    print(f'{{msg.topic}}: {{msg.payload}}')\n\nclient = mqtt.Client()\nclient.on_message = on_message\nclient.connect('{mqtt_host if mqtt_host != '0.0.0.0' else 'localhost'}', {mqtt_port})\nclient.subscribe('sensors/+/+/value')  # Generic mode\nclient.loop_forever()"
                    },
                    "modbus_python": {
                        "description": "Connect using pymodbus library",
                        "library": "pymodbus",
                        "install": "pip install pymodbus",
                        "code": f"from pymodbus.client import ModbusTcpClient\n\nclient = ModbusTcpClient('{modbus_host if modbus_host != '0.0.0.0' else 'localhost'}', port={modbus_port})\nif client.connect():\n    result = client.read_holding_registers(0, 10, slave=1)\n    if not result.isError():\n        print(f'Values: {{result.registers}}')\n    client.close()"
                    },
                    "websocket_javascript": {
                        "description": "Connect using native WebSocket API",
                        "library": "WebSocket (built-in)",
                        "code": f"const ws = new WebSocket('ws://localhost:{web_port}/ws');\n\nws.onmessage = (event) => {{\n    const data = JSON.parse(event.data);\n    console.log('Status:', data);\n}};\n\nws.onopen = () => {{\n    console.log('Connected to OT Simulator');\n}};"
                    }
                }
            }

            return web.json_response(endpoints)

        except Exception as e:
            logger.error(f"Error getting connection endpoints: {e}", exc_info=True)
            return web.json_response(
                {"error": str(e)},
                status=500
            )
