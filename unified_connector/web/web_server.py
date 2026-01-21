"""Web UI Server for Unified Connector.

Provides REST API and web interface for:
- Protocol server discovery and configuration
- ZeroBus target configuration
- Data flow monitoring
- Credential management
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from aiohttp import web
import aiohttp_cors

logger = logging.getLogger(__name__)


class WebServer:
    """Web server for configuration and monitoring."""

    def __init__(self, config: Dict[str, Any], bridge, discovery):
        """Initialize web server.

        Args:
            config: Application configuration
            bridge: UnifiedBridge instance
            discovery: DiscoveryService instance
        """
        self.config = config
        self.bridge = bridge
        self.discovery = discovery

        web_ui_config = config.get('web_ui', {})
        self.host = web_ui_config.get('host', '0.0.0.0')
        self.port = web_ui_config.get('port', 8080)

        self.app = None
        self.runner = None

    async def start(self):
        """Start web server."""
        self.app = web.Application()

        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })

        # API Routes
        routes = [
            # Discovery
            web.get('/api/discovery/servers', self.get_discovered_servers),
            web.post('/api/discovery/scan', self.trigger_discovery_scan),
            web.post('/api/discovery/test', self.test_server_connection),

            # Sources
            web.get('/api/sources', self.get_sources),
            web.post('/api/sources', self.add_source),
            web.delete('/api/sources/{name}', self.remove_source),
            web.put('/api/sources/{name}', self.update_source),

            # ZeroBus
            web.get('/api/zerobus/config', self.get_zerobus_config),
            web.post('/api/zerobus/config', self.update_zerobus_config),
            web.post('/api/zerobus/start', self.start_zerobus),
            web.post('/api/zerobus/stop', self.stop_zerobus),

            # Monitoring
            web.get('/api/metrics', self.get_metrics),
            web.get('/api/status', self.get_status),

            # Health
            web.get('/health', self.health_check),

            # Static files (Web UI)
            web.get('/', self.serve_index),
        ]

        for route in routes:
            resource = self.app.router.add_route(route.method, route.path, route.handler)
            cors.add(resource)

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

        logger.info(f"Web UI started on http://{self.host}:{self.port}")

    async def stop(self):
        """Stop web server."""
        if self.runner:
            await self.runner.cleanup()
        logger.info("Web UI stopped")

    # API Handlers

    async def get_discovered_servers(self, request: web.Request) -> web.Response:
        """Get list of discovered protocol servers."""
        protocol = request.query.get('protocol')
        servers = self.discovery.get_discovered_servers(protocol=protocol)

        return web.json_response({
            'servers': [s.to_dict() for s in servers],
            'count': len(servers)
        })

    async def trigger_discovery_scan(self, request: web.Request) -> web.Response:
        """Trigger immediate discovery scan."""
        try:
            asyncio.create_task(self.discovery.discover_all())
            return web.json_response({'status': 'ok', 'message': 'Discovery scan started'})
        except Exception as e:
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def test_server_connection(self, request: web.Request) -> web.Response:
        """Test connection to a specific server."""
        try:
            data = await request.json()
            protocol = data.get('protocol')
            host = data.get('host')
            port = data.get('port')

            if not all([protocol, host, port]):
                return web.json_response(
                    {'status': 'error', 'message': 'Missing required fields: protocol, host, port'},
                    status=400
                )

            result = await self.discovery.test_server_connection(protocol, host, port)
            return web.json_response(result)

        except Exception as e:
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def get_sources(self, request: web.Request) -> web.Response:
        """Get configured data sources."""
        sources = self.config.get('sources', [])
        return web.json_response({'sources': sources})

    async def add_source(self, request: web.Request) -> web.Response:
        """Add new data source."""
        try:
            data = await request.json()

            # Validate required fields
            required = ['name', 'protocol', 'endpoint']
            for field in required:
                if field not in data:
                    return web.json_response(
                        {'status': 'error', 'message': f'Missing required field: {field}'},
                        status=400
                    )

            # Add to bridge
            await self.bridge.add_source(
                source_name=data['name'],
                source_type=data['protocol'],
                source_config=data
            )

            # Update config file
            from unified_connector.core.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load()
            config['sources'].append(data)
            config_loader.save(config)

            return web.json_response({'status': 'ok', 'message': f"Source '{data['name']}' added"})

        except Exception as e:
            logger.error(f"Failed to add source: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def remove_source(self, request: web.Request) -> web.Response:
        """Remove data source."""
        try:
            source_name = request.match_info['name']

            # Remove from bridge
            await self.bridge.remove_source(source_name)

            # Update config file
            from unified_connector.core.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load()
            config['sources'] = [s for s in config['sources'] if s.get('name') != source_name]
            config_loader.save(config)

            return web.json_response({'status': 'ok', 'message': f"Source '{source_name}' removed"})

        except Exception as e:
            logger.error(f"Failed to remove source: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def update_source(self, request: web.Request) -> web.Response:
        """Update data source configuration."""
        try:
            source_name = request.match_info['name']
            data = await request.json()

            # Remove and re-add source
            await self.bridge.remove_source(source_name)
            await self.bridge.add_source(
                source_name=data['name'],
                source_type=data['protocol'],
                source_config=data
            )

            # Update config file
            from unified_connector.core.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load()
            config['sources'] = [
                data if s.get('name') == source_name else s
                for s in config['sources']
            ]
            config_loader.save(config)

            return web.json_response({'status': 'ok', 'message': f"Source '{source_name}' updated"})

        except Exception as e:
            logger.error(f"Failed to update source: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def get_zerobus_config(self, request: web.Request) -> web.Response:
        """Get ZeroBus configuration."""
        zerobus_config = self.config.get('zerobus', {})

        # Don't expose sensitive credentials
        safe_config = {**zerobus_config}
        if 'auth' in safe_config:
            safe_config['auth'] = {
                'client_id': safe_config['auth'].get('client_id', ''),
                'client_secret': '***' if safe_config['auth'].get('client_secret') else ''
            }

        return web.json_response(safe_config)

    async def update_zerobus_config(self, request: web.Request) -> web.Response:
        """Update ZeroBus configuration."""
        try:
            data = await request.json()

            # Store credentials securely
            from unified_connector.core.credential_manager import CredentialManager
            cred_manager = CredentialManager()

            if 'auth' in data:
                if 'client_id' in data['auth']:
                    cred_manager.update_credential('zerobus.client_id', data['auth']['client_id'])
                if 'client_secret' in data['auth']:
                    cred_manager.update_credential('zerobus.client_secret', data['auth']['client_secret'])

            # Update config file
            from unified_connector.core.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load()
            config['zerobus'] = {**config.get('zerobus', {}), **data}
            config_loader.save(config)

            return web.json_response({'status': 'ok', 'message': 'ZeroBus configuration updated'})

        except Exception as e:
            logger.error(f"Failed to update ZeroBus config: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def start_zerobus(self, request: web.Request) -> web.Response:
        """Start ZeroBus streaming."""
        try:
            result = await self.bridge.start_zerobus()
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Failed to start ZeroBus: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def stop_zerobus(self, request: web.Request) -> web.Response:
        """Stop ZeroBus streaming."""
        try:
            result = await self.bridge.stop_zerobus()
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Failed to stop ZeroBus: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def get_metrics(self, request: web.Request) -> web.Response:
        """Get connector metrics."""
        try:
            metrics = self.bridge.get_metrics()
            return web.json_response(metrics)
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def get_status(self, request: web.Request) -> web.Response:
        """Get connector status."""
        try:
            status = self.bridge.get_status()
            return web.json_response(status)
        except Exception as e:
            logger.error(f"Failed to get status: {e}", exc_info=True)
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({'status': 'healthy'})

    async def serve_index(self, request: web.Request) -> web.Response:
        """Serve web UI index page."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Unified OT/IoT Connector</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .card {
            background: white;
            padding: 20px;
            margin: 10px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 3px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }
        .status.connected {
            background: #28a745;
            color: white;
        }
        .status.disconnected {
            background: #dc3545;
            color: white;
        }
    </style>
</head>
<body>
    <h1>Unified OT/IoT Connector</h1>

    <div class="card">
        <h2>Status</h2>
        <p>Web UI is running.</p>
        <p>API endpoint: <code>/api</code></p>
    </div>

    <div class="card">
        <h2>API Endpoints</h2>
        <ul>
            <li><code>GET /api/discovery/servers</code> - List discovered servers</li>
            <li><code>POST /api/discovery/scan</code> - Trigger discovery scan</li>
            <li><code>GET /api/sources</code> - List configured sources</li>
            <li><code>POST /api/sources</code> - Add new source</li>
            <li><code>GET /api/metrics</code> - Get metrics</li>
            <li><code>GET /api/status</code> - Get status</li>
        </ul>
    </div>

    <div class="card">
        <h2>Quick Actions</h2>
        <button onclick="discoverServers()">Discover Servers</button>
        <button onclick="getMetrics()">View Metrics</button>
        <button onclick="getStatus()">View Status</button>
    </div>

    <div class="card">
        <h2>Response</h2>
        <pre id="response" style="background: #f8f9fa; padding: 10px; border-radius: 3px;"></pre>
    </div>

    <script>
        async function discoverServers() {
            try {
                const response = await fetch('/api/discovery/scan', { method: 'POST' });
                const data = await response.json();
                document.getElementById('response').textContent = JSON.stringify(data, null, 2);

                // Wait and fetch discovered servers
                setTimeout(async () => {
                    const serversResponse = await fetch('/api/discovery/servers');
                    const serversData = await serversResponse.json();
                    document.getElementById('response').textContent = JSON.stringify(serversData, null, 2);
                }, 2000);
            } catch (e) {
                document.getElementById('response').textContent = 'Error: ' + e.message;
            }
        }

        async function getMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                document.getElementById('response').textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                document.getElementById('response').textContent = 'Error: ' + e.message;
            }
        }

        async function getStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('response').textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                document.getElementById('response').textContent = 'Error: ' + e.message;
            }
        }
    </script>
</body>
</html>
        """
        return web.Response(text=html, content_type='text/html')
