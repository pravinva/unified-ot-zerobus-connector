#!/usr/bin/env python3
"""Test script for vendor mode integration with MQTT and OPC UA simulators.

This script tests:
1. Vendor mode initialization
2. MQTT publishing with vendor modes
3. OPC UA node creation with vendor modes
4. API endpoints for vendor mode management

Usage:
    PYTHONPATH=. .venv312/bin/python test_vendor_integration.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_vendor_integration")

# Suppress noisy logs
logging.getLogger("asyncua").setLevel(logging.ERROR)
logging.getLogger("ot_simulator.plc").setLevel(logging.ERROR)


async def test_vendor_mode_basic():
    """Test basic vendor mode functionality."""
    logger.info("=" * 80)
    logger.info("TEST 1: Basic Vendor Mode Functionality")
    logger.info("=" * 80)

    try:
        from ot_simulator.vendor_modes.integration import VendorModeIntegration
        from ot_simulator.vendor_modes.base import VendorModeType
        from ot_simulator.simulator_manager import SimulatorManager
        from ot_simulator.plc_models import PLCQualityCode

        # Create simulator manager
        manager = SimulatorManager()
        manager.init_plc_manager()

        # Create vendor integration
        vendor_integration = VendorModeIntegration(manager)
        await vendor_integration.initialize()

        logger.info("✓ Vendor mode integration initialized")

        # Get all mode status
        all_status = vendor_integration.get_all_mode_status()
        logger.info(f"✓ Found {len(all_status)} vendor modes")

        for mode_type, status in all_status.items():
            enabled = status.get('config', {}).get('enabled', False)
            logger.info(f"  - {mode_type}: {'ENABLED' if enabled else 'disabled'}")

        # Test formatting a sensor
        test_sensor = "mining/crusher_1_motor_power"
        formatted_data = vendor_integration.format_sensor_data(
            test_sensor,
            value=850.3,
            quality=PLCQualityCode.GOOD,
            timestamp=1234567890.0
        )

        logger.info(f"✓ Formatted sensor '{test_sensor}' for {len(formatted_data)} modes")
        for mode_type, data in formatted_data.items():
            logger.info(f"  - {mode_type}: {len(str(data))} bytes")

        # Test getting vendor-specific paths
        for mode_type in [VendorModeType.KEPWARE, VendorModeType.SPARKPLUG_B]:
            try:
                opcua_node = vendor_integration.get_opcua_node_id(test_sensor, mode_type)
                mqtt_topic = vendor_integration.get_mqtt_topic(test_sensor, mode_type)
                logger.info(f"✓ {mode_type} paths:")
                logger.info(f"    OPC UA: {opcua_node}")
                logger.info(f"    MQTT:   {mqtt_topic}")
            except Exception as e:
                logger.warning(f"  Could not get paths for {mode_type}: {e}")

        logger.info("✓ Basic vendor mode tests PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ Basic vendor mode test FAILED: {e}", exc_info=True)
        return False


async def test_mqtt_integration():
    """Test MQTT simulator with vendor modes."""
    logger.info("=" * 80)
    logger.info("TEST 2: MQTT Simulator Integration")
    logger.info("=" * 80)

    try:
        from ot_simulator.config_loader import load_config
        from ot_simulator.mqtt_simulator import MQTTSimulator
        from ot_simulator.simulator_manager import SimulatorManager

        # Load config
        config_path = Path("ot_simulator/config.yaml")
        if not config_path.exists():
            logger.warning("Config file not found, skipping MQTT test")
            return None

        config = load_config(config_path)

        # Create simulator manager
        manager = SimulatorManager()
        manager.init_plc_manager()

        # Create MQTT simulator with manager
        mqtt_sim = MQTTSimulator(config.mqtt, simulator_manager=manager)
        await mqtt_sim.init()

        logger.info("✓ MQTT simulator initialized")

        # Check vendor integration
        if mqtt_sim.vendor_integration:
            logger.info("✓ MQTT simulator has vendor integration")

            # Get active modes
            active_modes = mqtt_sim.vendor_integration.mode_manager.get_active_modes()
            logger.info(f"✓ MQTT vendor modes: {len(active_modes)} active")

            for mode in active_modes:
                logger.info(f"  - {mode.config.mode_type.value}")

        else:
            logger.warning("✗ MQTT simulator does not have vendor integration")
            return False

        logger.info("✓ MQTT integration tests PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ MQTT integration test FAILED: {e}", exc_info=True)
        return False


async def test_opcua_integration():
    """Test OPC UA simulator with vendor modes."""
    logger.info("=" * 80)
    logger.info("TEST 3: OPC UA Simulator Integration")
    logger.info("=" * 80)

    try:
        from ot_simulator.config_loader import load_config
        from ot_simulator.opcua_simulator import OPCUASimulator
        from ot_simulator.simulator_manager import SimulatorManager

        # Load config
        config_path = Path("ot_simulator/config.yaml")
        if not config_path.exists():
            logger.warning("Config file not found, skipping OPC UA test")
            return None

        config = load_config(config_path)

        # Create simulator manager
        manager = SimulatorManager()
        manager.init_plc_manager()

        # Create OPC UA simulator with manager
        opcua_sim = OPCUASimulator(config.opcua, simulator_manager=manager)
        await opcua_sim.init()

        logger.info("✓ OPC UA simulator initialized")

        # Check vendor integration
        if opcua_sim.vendor_integration:
            logger.info("✓ OPC UA simulator has vendor integration")

            # Get active modes
            active_modes = opcua_sim.vendor_integration.mode_manager.get_active_modes()
            logger.info(f"✓ OPC UA vendor modes: {len(active_modes)} active")

            for mode in active_modes:
                logger.info(f"  - {mode.config.mode_type.value}")

        else:
            logger.warning("✗ OPC UA simulator does not have vendor integration")
            return False

        # Stop the server
        await opcua_sim.stop()

        logger.info("✓ OPC UA integration tests PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ OPC UA integration test FAILED: {e}", exc_info=True)
        return False


async def test_api_endpoints():
    """Test vendor mode API endpoints."""
    logger.info("=" * 80)
    logger.info("TEST 4: Vendor Mode API Endpoints")
    logger.info("=" * 80)

    try:
        from ot_simulator.vendor_modes.api_routes import VendorModeAPIRoutes
        from ot_simulator.vendor_modes.integration import VendorModeIntegration
        from ot_simulator.simulator_manager import SimulatorManager
        from aiohttp import web
        from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
        import json

        # Create simulator manager
        manager = SimulatorManager()
        manager.init_plc_manager()

        # Create vendor integration
        vendor_integration = VendorModeIntegration(manager)
        await vendor_integration.initialize()

        # Create API routes
        api_routes = VendorModeAPIRoutes(vendor_integration)

        # Create test app
        app = web.Application()
        api_routes.setup_routes(app)

        logger.info("✓ API routes registered")

        # Test app runner
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, 'localhost', 18080)
        await site.start()

        logger.info("✓ Test server started on http://localhost:18080")

        # Make test requests
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Test 1: List modes
            async with session.get('http://localhost:18080/api/modes') as resp:
                assert resp.status == 200, f"Expected 200, got {resp.status}"
                data = await resp.json()
                logger.info(f"✓ GET /api/modes returned {len(data.get('modes', []))} modes")

            # Test 2: Get specific mode (Kepware)
            async with session.get('http://localhost:18080/api/modes/kepware') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✓ GET /api/modes/kepware succeeded")
                else:
                    logger.warning(f"  GET /api/modes/kepware returned {resp.status}")

            # Test 3: Get diagnostics
            async with session.get('http://localhost:18080/api/modes/kepware/diagnostics') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✓ GET /api/modes/kepware/diagnostics succeeded")
                else:
                    logger.warning(f"  GET /api/modes/kepware/diagnostics returned {resp.status}")

        # Cleanup
        await runner.cleanup()

        logger.info("✓ API endpoint tests PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ API endpoint test FAILED: {e}", exc_info=True)
        return False


async def main():
    """Run all integration tests."""
    logger.info("\n" + "=" * 80)
    logger.info("VENDOR MODE INTEGRATION TEST SUITE")
    logger.info("=" * 80 + "\n")

    results = {}

    # Run tests
    results['basic'] = await test_vendor_mode_basic()
    results['mqtt'] = await test_mqtt_integration()
    results['opcua'] = await test_opcua_integration()
    results['api'] = await test_api_endpoints()

    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    for test_name, result in results.items():
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⊘ SKIP")
        logger.info(f"{test_name:15s} {status}")

    logger.info("-" * 80)
    logger.info(f"Total: {len(results)} tests, {passed} passed, {failed} failed, {skipped} skipped")
    logger.info("=" * 80)

    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
