"""Web UI package for OT Simulator.

This package contains the modular web interface components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiohttp import web

from ot_simulator.web_ui.api_handlers import APIHandlers
from ot_simulator.web_ui.opcua_browser import OPCUABrowser
from ot_simulator.web_ui.wot_browser import handle_wot_browser
from ot_simulator.web_ui.templates import get_main_page_html
from ot_simulator.training_api import TrainingAPIHandler

# Import vendor mode API routes
try:
    from ot_simulator.vendor_modes.api_routes import VendorModeAPIRoutes
    from ot_simulator.vendor_modes.integration import VendorModeIntegration
    VENDOR_MODES_AVAILABLE = True
except ImportError:
    VendorModeAPIRoutes = None  # type: ignore
    VendorModeIntegration = None  # type: ignore
    VENDOR_MODES_AVAILABLE = False

if TYPE_CHECKING:
    from ot_simulator.simulator_manager import SimulatorManager


class EnhancedWebUI:
    """Enhanced professional web UI with real-time visualization.

    This is the main entry point for the web UI, delegating to modular components.
    """

    def __init__(self, config: Any, simulator_manager: SimulatorManager):
        """Initialize enhanced web UI.

        Args:
            config: Simulator configuration
            simulator_manager: SimulatorManager instance
        """
        self.config = config
        self.manager = simulator_manager
        self.app = web.Application()

        # Initialize modular components
        self.api_handlers = APIHandlers(config, simulator_manager)
        self.opcua_browser = OPCUABrowser(config, simulator_manager)
        self.training_api = TrainingAPIHandler(simulator_manager)

        # Initialize vendor mode API routes if available
        self.vendor_mode_api = None
        self.vendor_integration = None
        if VENDOR_MODES_AVAILABLE and simulator_manager:
            # Try to get existing vendor integration from protocol simulators
            vendor_integration = None
            for protocol in ['opcua', 'mqtt']:
                sim = simulator_manager.simulators.get(protocol)
                if sim and hasattr(sim, 'vendor_integration') and sim.vendor_integration:
                    vendor_integration = sim.vendor_integration
                    break

            # If not found, create new vendor integration
            if not vendor_integration:
                try:
                    vendor_integration = VendorModeIntegration(simulator_manager)
                    # Note: Will need to call await vendor_integration.initialize() later
                    self.vendor_integration = vendor_integration
                except Exception as e:
                    import logging
                    logging.getLogger("ot_simulator.web_ui").warning(f"Failed to create vendor integration: {e}")

            if vendor_integration:
                self.vendor_mode_api = VendorModeAPIRoutes(vendor_integration)

        # Setup routes
        self._setup_routes()

    async def initialize(self):
        """Initialize async components (like vendor integration)."""
        import logging
        logger = logging.getLogger("ot_simulator.web_ui")

        # Re-check for existing vendor_integration from protocol simulators
        # (they may have been initialized after web UI was created)
        # Prefer MQTT > OPC-UA since MQTT is where messages are captured
        if not self.vendor_integration and VENDOR_MODES_AVAILABLE and self.manager:
            for protocol in ['mqtt', 'opcua']:  # Check MQTT first!
                sim = self.manager.simulators.get(protocol)
                if sim and hasattr(sim, 'vendor_integration') and sim.vendor_integration:
                    logger.info(f"Found existing vendor_integration from {protocol} simulator")
                    self.vendor_integration = sim.vendor_integration
                    # Update vendor_mode_api to use this instance
                    if self.vendor_mode_api:
                        self.vendor_mode_api.vendor_integration = sim.vendor_integration
                    else:
                        self.vendor_mode_api = VendorModeAPIRoutes(sim.vendor_integration)
                        # Re-setup routes with the correct vendor integration
                        if self.vendor_mode_api:
                            self.vendor_mode_api.setup_routes(self.app)
                    break

        # DO NOT re-initialize if it already has been initialized
        # (checking for _initialized OR if mode_manager exists)
        if self.vendor_integration:
            if hasattr(self.vendor_integration, '_initialized') or hasattr(self.vendor_integration, 'mode_manager'):
                logger.info("Vendor integration already initialized, skipping re-initialization")
                return

            # Only initialize if brand new
            try:
                await self.vendor_integration.initialize()
                # Mark as initialized to avoid re-init
                self.vendor_integration._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize vendor integration: {e}")

    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/api/health", self.api_handlers.handle_health)
        self.app.router.add_get("/api/sensors", self.api_handlers.handle_list_sensors)
        self.app.router.add_get("/api/industries", self.api_handlers.handle_list_industries)
        self.app.router.add_get("/api/opcua/hierarchy", self.opcua_browser.handle_opcua_hierarchy)
        # OPC-UA Thing Description endpoint
        self.app.router.add_get("/api/opcua/thing-description", self.api_handlers.handle_opcua_thing_description)
        # W3C WoT Thing Description Browser
        self.app.router.add_get("/wot/browser", handle_wot_browser)
        # Raw data stream endpoint
        self.app.router.add_get("/api/raw-data-stream", self.api_handlers.handle_raw_data_stream)
        # Zero-Bus configuration endpoints
        self.app.router.add_post("/api/zerobus/config/load", self.api_handlers.handle_zerobus_config_load)
        self.app.router.add_post("/api/zerobus/config", self.api_handlers.handle_zerobus_config_save)
        self.app.router.add_post("/api/zerobus/test", self.api_handlers.handle_zerobus_test)
        # Zero-Bus streaming endpoints
        self.app.router.add_post("/api/zerobus/start", self.api_handlers.handle_zerobus_start)
        self.app.router.add_post("/api/zerobus/stop", self.api_handlers.handle_zerobus_stop)
        self.app.router.add_get("/api/zerobus/status", self.api_handlers.handle_zerobus_status)

        # Protocol clients/subscribers endpoints
        self.app.router.add_get("/api/protocols/opcua/clients", self.api_handlers.handle_get_opcua_clients)
        self.app.router.add_get("/api/protocols/mqtt/subscribers", self.api_handlers.handle_get_mqtt_subscribers)

        # Training API endpoints
        self.training_api.register_routes(self.app)

        # Vendor mode API endpoints
        if self.vendor_mode_api:
            self.vendor_mode_api.setup_routes(self.app)

    async def handle_index(self, request: web.Request) -> web.Response:
        """Serve enhanced professional UI with real-time charts and NLP."""
        html = get_main_page_html()
        return web.Response(text=html, content_type="text/html")


__all__ = ["EnhancedWebUI"]
