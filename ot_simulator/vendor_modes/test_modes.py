"""Test script for vendor modes.

Tests Kepware, Sparkplug B, and Honeywell modes with sample data.
"""

import asyncio
import logging
import time
from pathlib import Path

from ot_simulator.plc_models import PLCConfig, PLCSimulator, PLCQualityCode, PLCVendor
from ot_simulator.sensor_models import SensorConfig, SensorSimulator, SensorType
from ot_simulator.vendor_modes.base import ModeConfig, VendorModeType
from ot_simulator.vendor_modes.kepware import KepwareMode
from ot_simulator.vendor_modes.sparkplug_b import SparkplugBMode
from ot_simulator.vendor_modes.honeywell import HoneywellMode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_kepware_mode():
    """Test Kepware mode."""
    logger.info("=" * 60)
    logger.info("TESTING KEPWARE MODE")
    logger.info("=" * 60)

    # Create configuration
    config = ModeConfig(
        mode_type=VendorModeType.KEPWARE,
        enabled=True,
        opcua_enabled=True,
        opcua_port=49320,
        mqtt_enabled=True,
        mqtt_topic_prefix="kepware",
        settings={
            "iot_gateway_format": True,
            "batch_by_device": True,
        }
    )

    # Initialize mode
    mode = KepwareMode(config)
    success = await mode.initialize()
    assert success, "Kepware mode initialization failed"
    logger.info("✓ Kepware mode initialized")

    # Create test PLC
    plc_config = PLCConfig(
        vendor=PLCVendor.SIEMENS,
        model="S7-1500",
        name="PLC_MINING_CRUSH",
        scan_cycle_ms=50,
    )
    # PLCSimulator requires sensor_manager, using None for test
    plc_instance = type('PLCSimulator', (), {'config': plc_config})()

    # Register test sensor
    mode.register_sensor("crusher_1_motor_power", plc_instance, "mining")
    logger.info("✓ Registered sensor with Kepware mode")

    # Format sample data
    formatted = mode.format_sensor_data(
        "crusher_1_motor_power",
        850.3,
        PLCQualityCode.GOOD,
        time.time(),
        plc_instance,
        unit="kW",
        sensor_type="power",
        industry="mining",
    )

    logger.info(f"Formatted data: {formatted}")

    # Get node ID
    node_id = mode.get_opcua_node_id("crusher_1_motor_power", plc_instance, industry="mining")
    logger.info(f"OPC UA Node ID: {node_id}")

    # Get MQTT topic
    topic = mode.get_mqtt_topic("crusher_1_motor_power", plc_instance, industry="mining")
    logger.info(f"MQTT Topic: {topic}")

    # Get diagnostics
    diagnostics = mode.get_diagnostics()
    logger.info(f"Diagnostics: {diagnostics}")

    await mode.shutdown()
    logger.info("✓ Kepware mode test completed\n")


async def test_sparkplug_b_mode():
    """Test Sparkplug B mode."""
    logger.info("=" * 60)
    logger.info("TESTING SPARKPLUG B MODE")
    logger.info("=" * 60)

    # Create configuration
    config = ModeConfig(
        mode_type=VendorModeType.SPARKPLUG_B,
        enabled=True,
        mqtt_enabled=True,
        settings={
            "group_id": "DatabricksDemo",
            "edge_node_id": "OTSimulator01",
            "cov_threshold": 0.01,
        }
    )

    # Initialize mode
    mode = SparkplugBMode(config)
    success = await mode.initialize()
    assert success, "Sparkplug B mode initialization failed"
    logger.info("✓ Sparkplug B mode initialized")

    # Create test PLC
    plc_config = PLCConfig(
        vendor=PLCVendor.ROCKWELL,
        model="ControlLogix 5580",
        name="PLC_MINING_CRUSH",
        scan_cycle_ms=50,
    )
    # PLCSimulator requires sensor_manager, using None for test
    plc_instance = type('PLCSimulator', (), {'config': plc_config})()

    # Register test sensor
    mode.register_sensor(
        "crusher_1_motor_power",
        plc_instance,
        "mining",
        "power",
        "kW"
    )
    logger.info("✓ Registered sensor with Sparkplug B mode")

    # Generate NBIRTH
    nbirth = mode.generate_nbirth()
    logger.info(f"NBIRTH: {nbirth}")

    # Generate DBIRTH for device
    dbirth = mode.generate_dbirth("MiningAssets")
    logger.info(f"DBIRTH: {dbirth}")

    # Format sample data (DDATA)
    formatted = mode.format_sensor_data(
        "crusher_1_motor_power",
        850.3,
        PLCQualityCode.GOOD,
        time.time(),
        plc_instance,
        unit="kW",
        sensor_type="power",
        industry="mining",
    )

    logger.info(f"DDATA: {formatted}")

    # Get MQTT topic
    topic = mode.get_mqtt_topic("crusher_1_motor_power", plc_instance, industry="mining")
    logger.info(f"MQTT Topic: {topic}")

    # Get diagnostics
    diagnostics = mode.get_diagnostics()
    logger.info(f"Diagnostics: {diagnostics}")

    await mode.shutdown()
    logger.info("✓ Sparkplug B mode test completed\n")


async def test_honeywell_mode():
    """Test Honeywell Experion mode."""
    logger.info("=" * 60)
    logger.info("TESTING HONEYWELL EXPERION MODE")
    logger.info("=" * 60)

    # Create configuration
    config = ModeConfig(
        mode_type=VendorModeType.HONEYWELL,
        enabled=True,
        opcua_enabled=True,
        opcua_port=4897,
        mqtt_enabled=True,
        settings={
            "server_name": "MINE_A_EXPERION_PKS",
            "pks_version": "R520",
        }
    )

    # Initialize mode
    mode = HoneywellMode(config)
    success = await mode.initialize()
    assert success, "Honeywell mode initialization failed"
    logger.info("✓ Honeywell Experion mode initialized")

    # Create test PLC
    plc_config = PLCConfig(
        vendor=PLCVendor.SCHNEIDER,
        model="Modicon M580",
        name="PLC_MINING_CRUSH",
        scan_cycle_ms=100,
    )
    # PLCSimulator requires sensor_manager, using None for test
    plc_instance = type('PLCSimulator', (), {'config': plc_config})()

    # Create sensor config
    sensor_config = SensorConfig(
        name="crusher_1_motor_power",
        sensor_type=SensorType.POWER,
        unit="kW",
        min_value=0,
        max_value=1200,
        nominal_value=850,
    )

    # Register test sensor
    mode.register_sensor("crusher_1_motor_power", plc_instance, sensor_config)
    logger.info("✓ Registered sensor with Honeywell mode")

    # Format sample data
    formatted = mode.format_sensor_data(
        "crusher_1_motor_power",
        850.3,
        PLCQualityCode.GOOD,
        time.time(),
        plc_instance,
        sensor_config=sensor_config,
    )

    logger.info(f"Formatted data: {formatted}")

    # Get node ID
    node_id = mode.get_opcua_node_id("crusher_1_motor_power", plc_instance, industry="mining")
    logger.info(f"OPC UA Node ID: {node_id}")

    # Get all node IDs for composite point
    all_node_ids = mode.get_all_node_ids("CRUSHER_1_MOTOR_POWER", "FIM_01")
    logger.info(f"All node IDs ({len(all_node_ids)}): {all_node_ids[:3]}...")

    # Get MQTT topic
    topic = mode.get_mqtt_topic("crusher_1_motor_power", plc_instance, industry="mining")
    logger.info(f"MQTT Topic: {topic}")

    # Get diagnostics
    diagnostics = mode.get_diagnostics()
    logger.info(f"Diagnostics: {diagnostics}")

    await mode.shutdown()
    logger.info("✓ Honeywell Experion mode test completed\n")


async def main():
    """Run all tests."""
    logger.info("Starting vendor mode tests...\n")

    try:
        await test_kepware_mode()
        await test_sparkplug_b_mode()
        await test_honeywell_mode()

        logger.info("=" * 60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
