"""Factory for creating and managing vendor modes."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ot_simulator.vendor_modes.base import (
    ModeConfig,
    ModeStatus,
    VendorMode,
    VendorModeType,
)
from ot_simulator.vendor_modes.kepware import KepwareMode
from ot_simulator.vendor_modes.sparkplug_b import SparkplugBMode
from ot_simulator.vendor_modes.honeywell import HoneywellMode

logger = logging.getLogger("ot_simulator.vendor_factory")


class VendorModeFactory:
    """Factory for creating vendor mode instances."""

    @staticmethod
    def create_mode(config: ModeConfig) -> VendorMode:
        """Create a vendor mode instance based on configuration.

        Args:
            config: Mode configuration

        Returns:
            VendorMode instance

        Raises:
            ValueError: If mode type is not supported
        """
        mode_type = config.mode_type

        if mode_type == VendorModeType.KEPWARE:
            return KepwareMode(config)
        elif mode_type == VendorModeType.SPARKPLUG_B:
            return SparkplugBMode(config)
        elif mode_type == VendorModeType.HONEYWELL:
            return HoneywellMode(config)
        elif mode_type == VendorModeType.GENERIC:
            # Generic mode uses base implementation
            from ot_simulator.vendor_modes.generic import GenericMode
            return GenericMode(config)
        else:
            raise ValueError(f"Unsupported vendor mode type: {mode_type}")

    @staticmethod
    def get_supported_modes() -> List[VendorModeType]:
        """Get list of supported vendor mode types."""
        return [
            VendorModeType.GENERIC,
            VendorModeType.KEPWARE,
            VendorModeType.SPARKPLUG_B,
            VendorModeType.HONEYWELL,
        ]


class VendorModeManager:
    """Manages multiple vendor modes simultaneously."""

    def __init__(self):
        self.modes: Dict[VendorModeType, VendorMode] = {}
        self._initialized = False

    async def initialize(self, mode_configs: List[ModeConfig]):
        """Initialize all configured vendor modes.

        Args:
            mode_configs: List of mode configurations
        """
        logger.info(f"Initializing {len(mode_configs)} vendor modes...")

        for config in mode_configs:
            if not config.enabled:
                logger.info(f"Skipping disabled mode: {config.mode_type}")
                continue

            try:
                mode = VendorModeFactory.create_mode(config)
                success = await mode.initialize()

                if success:
                    self.modes[config.mode_type] = mode
                    logger.info(f"Initialized mode: {config.mode_type}")
                else:
                    logger.error(f"Failed to initialize mode: {config.mode_type}")

            except Exception as e:
                logger.error(
                    f"Error creating mode {config.mode_type}: {e}",
                    exc_info=True
                )

        self._initialized = True
        logger.info(f"Vendor mode manager initialized with {len(self.modes)} active modes")

    async def shutdown(self):
        """Shutdown all vendor modes."""
        logger.info("Shutting down vendor mode manager...")

        for mode_type, mode in self.modes.items():
            try:
                await mode.shutdown()
                logger.info(f"Shutdown mode: {mode_type}")
            except Exception as e:
                logger.error(f"Error shutting down mode {mode_type}: {e}")

        self.modes.clear()
        self._initialized = False

    def get_mode(self, mode_type: VendorModeType) -> Optional[VendorMode]:
        """Get a specific vendor mode.

        Args:
            mode_type: Type of vendor mode

        Returns:
            VendorMode instance or None if not active
        """
        return self.modes.get(mode_type)

    def get_active_modes(self) -> List[VendorMode]:
        """Get list of all active vendor modes."""
        return list(self.modes.values())

    def get_mode_status(self, mode_type: VendorModeType) -> Dict:
        """Get status of a specific mode."""
        mode = self.get_mode(mode_type)
        if mode:
            return mode.get_status()
        return {
            "config": {"mode_type": mode_type, "enabled": False},
            "metrics": {"status": ModeStatus.DISABLED},
        }

    def get_all_status(self) -> Dict[VendorModeType, Dict]:
        """Get status of all configured modes."""
        status = {}
        for mode_type in VendorModeFactory.get_supported_modes():
            status[mode_type] = self.get_mode_status(mode_type)
        return status

    async def enable_mode(self, mode_type: VendorModeType, config: ModeConfig) -> bool:
        """Enable and initialize a vendor mode dynamically.

        Args:
            mode_type: Type of vendor mode
            config: Mode configuration

        Returns:
            True if enabled successfully
        """
        if mode_type in self.modes:
            logger.warning(f"Mode {mode_type} already active")
            return True

        try:
            mode = VendorModeFactory.create_mode(config)
            success = await mode.initialize()

            if success:
                self.modes[mode_type] = mode
                logger.info(f"Dynamically enabled mode: {mode_type}")
                return True
            else:
                logger.error(f"Failed to enable mode: {mode_type}")
                return False

        except Exception as e:
            logger.error(f"Error enabling mode {mode_type}: {e}", exc_info=True)
            return False

    async def disable_mode(self, mode_type: VendorModeType) -> bool:
        """Disable and shutdown a vendor mode.

        Args:
            mode_type: Type of vendor mode

        Returns:
            True if disabled successfully
        """
        mode = self.modes.get(mode_type)
        if not mode:
            logger.warning(f"Mode {mode_type} not active")
            return True

        try:
            await mode.shutdown()
            del self.modes[mode_type]
            logger.info(f"Disabled mode: {mode_type}")
            return True

        except Exception as e:
            logger.error(f"Error disabling mode {mode_type}: {e}", exc_info=True)
            return False

    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized
