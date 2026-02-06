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
        app.router.add_get("/api/modes/{mode_type}/diagnostics", self.handle_get_diagnostics)
        app.router.add_get("/api/modes/{mode_type}/status", self.handle_get_mode_status)

        # Utility endpoints
        app.router.add_get("/api/modes/sensor/{sensor_path}/paths", self.handle_get_sensor_paths)

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
