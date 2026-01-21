"""Unified Bridge - Enterprise OT/IoT Connector Core.

Orchestrates data flow from protocol sources to Databricks:
    Protocol Clients → Tag Normalization → Backpressure → ZeroBus → Delta Tables

Features:
- Multi-protocol support (OPC-UA, MQTT, Modbus)
- Tag normalization (ISA-95 hierarchies)
- Per-source ZeroBus targets (different tables per source)
- Credential encryption
- Auto-reconnection with exponential backoff
- Backpressure handling with disk spooling
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from unified_connector.protocols.base import ProtocolClient, ProtocolRecord, ProtocolType
from unified_connector.protocols.factory import create_protocol_client
from unified_connector.normalizer import get_normalization_manager
from unified_connector.core.backpressure import BackpressureManager
from unified_connector.core.zerobus_client import ZeroBusClient

logger = logging.getLogger(__name__)


class UnifiedBridge:
    """
    Unified bridge orchestrating OT/IoT data ingestion to Databricks.

    Architecture:
        Protocol Sources → Tag Normalization → Backpressure Queue → ZeroBus Batching → Delta Tables

    Key Features:
        - Per-source ZeroBus targets (route different sources to different tables)
        - Tag normalization with ISA-95/Purdue Model hierarchies
        - Credential encryption at rest
        - Automatic reconnection with exponential backoff
        - Backpressure with disk spooling for resilience
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize unified bridge.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.sources = config.get('sources', [])

        # ZeroBus configuration
        self.zerobus_config = config.get('zerobus', {})
        self.zerobus_enabled = self.zerobus_config.get('enabled', False)

        # Tag normalization
        self.normalization_config = config.get('normalization', {})
        self.normalization_enabled = self.normalization_config.get('enabled', True)

        # Initialize normalizer if enabled
        if self.normalization_enabled:
            self.norm_manager = get_normalization_manager()
            self.norm_manager.configure(self.normalization_config)
            logger.info("Tag normalization enabled")
        else:
            self.norm_manager = None
            logger.info("Tag normalization disabled")

        # Initialize backpressure manager
        self.backpressure = BackpressureManager(config.get('backpressure', {}))

        # ZeroBus clients (one per unique target)
        self.zerobus_clients: Dict[str, ZeroBusClient] = {}

        # Protocol clients
        self.clients: Dict[str, ProtocolClient] = {}
        self.client_tasks: Dict[str, asyncio.Task] = {}

        # Batch processing tasks (one per ZeroBus target)
        self.batch_tasks: Dict[str, asyncio.Task] = {}

        # Batch settings
        self.batch_size = self.zerobus_config.get('batch', {}).get('max_records', 1000)
        self.batch_timeout_sec = self.zerobus_config.get('batch', {}).get('timeout_seconds', 5.0)

        # Reconnection settings
        self.reconnect_enabled = True
        self.reconnect_initial_delay_sec = 1.0
        self.reconnect_max_delay_sec = 300.0
        self.reconnect_multiplier = 2.0

        # Metrics
        self.metrics = {
            'records_received': 0,
            'records_normalized': 0,
            'records_enqueued': 0,
            'records_dropped': 0,
            'batches_sent': 0,
            'reconnections': 0,
        }

        self._shutdown = False

        logger.info(f"UnifiedBridge initialized: {len(self.sources)} sources configured")

    async def start(self):
        """Start all components."""
        logger.info("Starting UnifiedBridge...")

        # Initialize ZeroBus clients if enabled
        if self.zerobus_enabled:
            logger.info("ZeroBus enabled - initializing connections...")
            await self._initialize_zerobus_clients()
        else:
            logger.info("ZeroBus disabled - data collection only mode")

        # Start protocol clients
        for source_config in self.sources:
            source_name = source_config.get('name', 'unknown')
            if not source_config.get('enabled', True):
                logger.info(f"Source '{source_name}' is disabled, skipping")
                continue

            try:
                await self._start_client(source_config)
                logger.info(f"✓ Started source: {source_name}")
            except Exception as e:
                logger.error(f"Failed to start source {source_name}: {e}")
                # Continue with other sources

        # Start batch processors if ZeroBus enabled
        if self.zerobus_enabled:
            for target_id in self.zerobus_clients.keys():
                task = asyncio.create_task(self._batch_processor(target_id))
                self.batch_tasks[target_id] = task
                logger.info(f"Batch processor started for target: {target_id}")

        logger.info(f"✓ UnifiedBridge started with {len(self.clients)} active sources")

    async def _initialize_zerobus_clients(self):
        """Initialize ZeroBus clients for each unique target."""
        # Get default target
        default_target = self.zerobus_config.get('default_target', {})

        # Get per-source targets
        source_targets = self.zerobus_config.get('source_targets', {})

        # Build unique targets
        targets = {}

        # Add default target
        if default_target.get('workspace_host'):
            target_id = self._get_target_id(default_target)
            targets[target_id] = default_target

        # Add per-source targets
        for source_name, target_config in source_targets.items():
            # Merge with default config
            merged_target = {**default_target, **target_config}
            target_id = self._get_target_id(merged_target)
            targets[target_id] = merged_target

        # Create ZeroBus clients for each target
        for target_id, target_config in targets.items():
            try:
                # Build ZeroBus config for this target
                zb_config = {
                    'zerobus': {
                        'enabled': True,
                        'workspace_host': target_config['workspace_host'],
                        'target': {
                            'catalog': target_config.get('catalog', 'main'),
                            'schema': target_config.get('schema', 'iot_data'),
                            'table': target_config.get('table', 'sensor_readings'),
                        },
                        'auth': self.zerobus_config.get('auth', {}),
                        'batch': self.zerobus_config.get('batch', {}),
                    }
                }

                client = ZeroBusClient(zb_config)
                await client.connect()

                self.zerobus_clients[target_id] = client
                logger.info(f"✓ ZeroBus client connected: {target_id}")

            except Exception as e:
                logger.error(f"Failed to initialize ZeroBus client for {target_id}: {e}")

    def _get_target_id(self, target_config: Dict[str, Any]) -> str:
        """Generate unique ID for ZeroBus target.

        Args:
            target_config: Target configuration dict

        Returns:
            Unique target ID string
        """
        workspace = target_config.get('workspace_host', '')
        catalog = target_config.get('catalog', 'main')
        schema = target_config.get('schema', 'iot_data')
        table = target_config.get('table', 'sensor_readings')

        # Extract workspace ID from URL
        workspace_id = workspace.split('//')[1].split('.')[0] if '//' in workspace else workspace

        return f"{workspace_id}.{catalog}.{schema}.{table}"

    def _get_target_for_source(self, source_name: str) -> str:
        """Get ZeroBus target ID for a source.

        Args:
            source_name: Name of the source

        Returns:
            Target ID
        """
        # Check if source has specific target
        source_targets = self.zerobus_config.get('source_targets', {})
        if source_name in source_targets:
            target_config = {
                **self.zerobus_config.get('default_target', {}),
                **source_targets[source_name]
            }
            return self._get_target_id(target_config)

        # Use default target
        default_target = self.zerobus_config.get('default_target', {})
        return self._get_target_id(default_target)

    async def _start_client(self, source_config: Dict[str, Any]):
        """Start a single protocol client with reconnection loop.

        Args:
            source_config: Source configuration dict
        """
        source_name = source_config.get('name', 'unknown')
        protocol_type = source_config.get('protocol', 'opcua')

        # Add normalization flag to source config
        source_config['normalization_enabled'] = self.normalization_enabled

        # Create protocol client
        client = create_protocol_client(
            protocol_type=protocol_type,
            source_name=source_name,
            endpoint=source_config['endpoint'],
            config=source_config,
            on_record=self._on_record,
            on_stats=self._on_stats
        )

        self.clients[source_name] = client

        # Start client with reconnection loop
        task = asyncio.create_task(self._client_lifecycle(source_name, client))
        self.client_tasks[source_name] = task

    async def _client_lifecycle(self, source_name: str, client: ProtocolClient):
        """Manage protocol client lifecycle with automatic reconnection.

        Args:
            source_name: Name of the source
            client: Protocol client instance
        """
        reconnect_delay = self.reconnect_initial_delay_sec

        while not self._shutdown:
            try:
                logger.info(f"[{source_name}] Connecting to {client.endpoint}...")
                await client.connect()
                logger.info(f"[{source_name}] ✓ Connected")

                # Start subscription/polling
                logger.info(f"[{source_name}] Starting data collection...")
                await client.subscribe()

                # Keep running until shutdown
                while not self._shutdown:
                    await asyncio.sleep(1)

                # Cleanup on shutdown
                await client.disconnect()
                reconnect_delay = self.reconnect_initial_delay_sec

                if self._shutdown:
                    break

            except Exception as e:
                logger.error(f"[{source_name}] Error: {e}")

                # Cleanup
                try:
                    await client.stop()
                    await client.disconnect()
                except Exception:
                    pass

                if not self.reconnect_enabled or self._shutdown:
                    break

                # Exponential backoff with jitter
                jitter = reconnect_delay * 0.1 * (2 * (time.time() % 1) - 0.5)
                sleep_time = min(reconnect_delay + jitter, self.reconnect_max_delay_sec)

                logger.warning(f"[{source_name}] Reconnecting in {sleep_time:.1f}s...")
                self.metrics['reconnections'] += 1

                await asyncio.sleep(sleep_time)

                # Increase backoff
                reconnect_delay = min(
                    reconnect_delay * self.reconnect_multiplier,
                    self.reconnect_max_delay_sec
                )

        logger.info(f"[{source_name}] Client lifecycle ended")

    def _on_record(self, record: ProtocolRecord):
        """Callback when protocol client receives a record.

        Args:
            record: Protocol record
        """
        self.metrics['records_received'] += 1

        # Convert to dict
        record_dict = {
            'timestamp': record.timestamp,
            'source_name': record.source_name,
            'protocol_type': record.protocol_type.value,
            'tag_id': record.tag_id,
            'tag_name': record.tag_name,
            'value': record.value,
            'quality': record.quality,
            'metadata': record.metadata,
        }

        # Apply normalization if enabled
        if self.normalization_enabled and self.norm_manager:
            try:
                normalizer = self.norm_manager.get_normalizer(record.protocol_type.value)
                if normalizer:
                    # Create raw data format expected by normalizer
                    raw_data = self._protocol_record_to_raw_data(record)
                    normalized_tag = normalizer.normalize(raw_data)

                    # Update record with normalized values
                    record_dict['tag_path'] = normalized_tag.tag_path
                    record_dict['tag_id'] = normalized_tag.tag_id
                    record_dict['data_type'] = normalized_tag.data_type.value
                    record_dict['quality'] = normalized_tag.quality.value

                    self.metrics['records_normalized'] += 1
            except Exception as e:
                logger.warning(f"Normalization failed for {record.tag_name}: {e}")

        # Enqueue for ZeroBus
        asyncio.create_task(self._enqueue_record(record_dict))

    def _protocol_record_to_raw_data(self, record: ProtocolRecord) -> Dict[str, Any]:
        """Convert ProtocolRecord to raw data format for normalizers.

        Args:
            record: Protocol record

        Returns:
            Raw data dict
        """
        return {
            'value': record.value,
            'timestamp': record.timestamp,
            'quality': record.quality,
            'tag_name': record.tag_name,
            'tag_id': record.tag_id,
            'source_name': record.source_name,
            'metadata': record.metadata or {},
        }

    async def _enqueue_record(self, record: Dict[str, Any]):
        """Enqueue record to backpressure queue.

        Args:
            record: Record dict
        """
        success = await self.backpressure.enqueue(record)
        if success:
            self.metrics['records_enqueued'] += 1
        else:
            self.metrics['records_dropped'] += 1

    def _on_stats(self, stats: Dict[str, Any]):
        """Callback for protocol client statistics.

        Args:
            stats: Statistics dict
        """
        logger.debug(f"Protocol stats: {stats}")

    async def _batch_processor(self, target_id: str):
        """Process records from backpressure queue in batches to ZeroBus.

        Args:
            target_id: ZeroBus target identifier
        """
        logger.info(f"Batch processor started for {target_id}")
        batch: List[Any] = []
        last_flush_time = time.time()

        zerobus_client = self.zerobus_clients.get(target_id)
        if not zerobus_client:
            logger.error(f"No ZeroBus client for target {target_id}")
            return

        while not self._shutdown:
            try:
                # Try to dequeue with timeout
                try:
                    record = await asyncio.wait_for(
                        self.backpressure.dequeue(),
                        timeout=1.0
                    )

                    if record is not None:
                        # Convert to ZeroBus message format
                        message = self._to_zerobus_message(record)
                        batch.append(message)

                except asyncio.TimeoutError:
                    pass

                # Flush batch if size or timeout reached
                current_time = time.time()
                should_flush = (
                    len(batch) >= self.batch_size or
                    (len(batch) > 0 and (current_time - last_flush_time) >= self.batch_timeout_sec)
                )

                if should_flush:
                    logger.debug(f"Flushing batch of {len(batch)} records to {target_id}")
                    success = await zerobus_client.send_batch(batch)

                    if success:
                        self.metrics['batches_sent'] += 1
                        batch.clear()
                        last_flush_time = current_time
                    else:
                        logger.warning(f"ZeroBus send failed for {target_id}, will retry")
                        await asyncio.sleep(5.0)

            except Exception as e:
                logger.error(f"Batch processor error for {target_id}: {e}")
                await asyncio.sleep(1.0)

        # Flush remaining records on shutdown
        if batch:
            logger.info(f"Flushing final batch of {len(batch)} records to {target_id}")
            await zerobus_client.send_batch(batch)

        logger.info(f"Batch processor stopped for {target_id}")

    def _to_zerobus_message(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal record format to ZeroBus message.

        Args:
            record: Internal record dict

        Returns:
            ZeroBus message dict
        """
        timestamp_us = record.get('timestamp', int(time.time() * 1_000_000))

        return {
            'event_time': timestamp_us,
            'ingest_time': int(time.time() * 1_000_000),
            'source_name': record.get('source_name', ''),
            'protocol_type': record.get('protocol_type', ''),
            'tag_id': record.get('tag_id', ''),
            'tag_name': record.get('tag_name', ''),
            'tag_path': record.get('tag_path', record.get('tag_name', '')),
            'value': str(record.get('value', '')),
            'value_num': record.get('value_num'),
            'data_type': record.get('data_type', 'string'),
            'quality': record.get('quality', 'unknown'),
            'metadata': record.get('metadata', {}),
        }

    async def stop(self):
        """Stop all components gracefully."""
        logger.info("Stopping UnifiedBridge...")
        self._shutdown = True

        # Stop all protocol clients
        for source_name, client in self.clients.items():
            try:
                logger.info(f"Stopping source: {source_name}")
                await client.stop()
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error stopping {source_name}: {e}")

        # Wait for client tasks
        if self.client_tasks:
            await asyncio.gather(*self.client_tasks.values(), return_exceptions=True)

        # Stop batch processors
        if self.batch_tasks:
            for task in self.batch_tasks.values():
                task.cancel()
            await asyncio.gather(*self.batch_tasks.values(), return_exceptions=True)

        # Close ZeroBus clients
        for target_id, client in self.zerobus_clients.items():
            try:
                await client.close()
                logger.info(f"Closed ZeroBus client: {target_id}")
            except Exception as e:
                logger.error(f"Error closing ZeroBus client {target_id}: {e}")

        logger.info("✓ UnifiedBridge stopped")

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all components.

        Returns:
            Metrics dict
        """
        return {
            'bridge': self.metrics,
            'backpressure': self.backpressure.get_metrics(),
            'zerobus_targets': {
                target_id: client.get_metrics()
                for target_id, client in self.zerobus_clients.items()
            },
            'clients': {
                name: {
                    'connected': client._client is not None if hasattr(client, '_client') else False,
                    'protocol': client.protocol_type.value,
                    'endpoint': client.endpoint,
                }
                for name, client in self.clients.items()
            }
        }

    async def add_source(self, source_name: str, source_type: str, source_config: Dict[str, Any]):
        """Add a new data source dynamically.

        Args:
            source_name: Unique name for the source
            source_type: Protocol type ('opcua', 'mqtt', 'modbus')
            source_config: Source configuration dict

        Raises:
            ValueError: If source already exists or config is invalid
        """
        if source_name in self.clients:
            raise ValueError(f"Source '{source_name}' already exists")

        logger.info(f"Adding new source: {source_name} (type: {source_type})")

        # Build full source config
        full_config = {
            'name': source_name,
            'protocol': source_type,
            'enabled': True,
            **source_config
        }

        # Add to internal sources list
        self.sources.append(full_config)

        # Start the client if bridge is running
        if not self._shutdown:
            try:
                await self._start_client(full_config)
                logger.info(f"✓ Source '{source_name}' added and started successfully")
            except Exception as e:
                # Remove from sources list if start failed
                self.sources.remove(full_config)
                logger.error(f"Failed to start source '{source_name}': {e}")
                raise ValueError(f"Failed to start source: {e}")
        else:
            logger.info(f"✓ Source '{source_name}' added (will start when bridge starts)")

    async def remove_source(self, source_name: str):
        """Remove an existing data source dynamically.

        Args:
            source_name: Name of the source to remove

        Raises:
            ValueError: If source doesn't exist
        """
        if source_name not in self.clients:
            raise ValueError(f"Source '{source_name}' not found")

        logger.info(f"Removing source: {source_name}")

        # Stop the client
        client = self.clients[source_name]
        try:
            await client.stop()
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error stopping source '{source_name}': {e}")

        # Cancel the task
        if source_name in self.client_tasks:
            task = self.client_tasks[source_name]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.client_tasks[source_name]

        # Remove from clients dict
        del self.clients[source_name]

        # Remove from sources list
        self.sources = [s for s in self.sources if s.get('name') != source_name]

        logger.info(f"✓ Source '{source_name}' removed successfully")

    async def start_zerobus(self) -> Dict[str, Any]:
        """Start ZeroBus streaming dynamically.

        Returns:
            dict: Status message with success/error
        """
        try:
            if self.zerobus_enabled:
                return {'status': 'ok', 'message': 'ZeroBus already enabled'}

            logger.info("Starting ZeroBus streaming...")

            # Initialize ZeroBus clients
            await self._initialize_zerobus_clients()

            # Start batch processors
            for target_id in self.zerobus_clients.keys():
                task = asyncio.create_task(self._batch_processor(target_id))
                self.batch_tasks[target_id] = task
                logger.info(f"Batch processor started for target: {target_id}")

            self.zerobus_enabled = True

            logger.info("✓ ZeroBus streaming started successfully")
            return {'status': 'ok', 'message': 'ZeroBus streaming started successfully'}

        except Exception as e:
            logger.error(f"Failed to start ZeroBus: {e}", exc_info=True)
            return {'status': 'error', 'message': f'Failed to start ZeroBus: {str(e)}'}

    async def stop_zerobus(self) -> Dict[str, Any]:
        """Stop ZeroBus streaming dynamically.

        Returns:
            dict: Status message with success/error
        """
        try:
            if not self.zerobus_enabled:
                return {'status': 'ok', 'message': 'ZeroBus already disabled'}

            logger.info("Stopping ZeroBus streaming...")

            # Stop batch processors
            if self.batch_tasks:
                for task in self.batch_tasks.values():
                    task.cancel()
                await asyncio.gather(*self.batch_tasks.values(), return_exceptions=True)
                self.batch_tasks.clear()
                logger.info("Batch processors stopped")

            # Close ZeroBus clients
            for target_id, client in self.zerobus_clients.items():
                try:
                    await client.close()
                    logger.info(f"Closed ZeroBus client: {target_id}")
                except Exception as e:
                    logger.error(f"Error closing ZeroBus client {target_id}: {e}")

            self.zerobus_clients.clear()
            self.zerobus_enabled = False

            logger.info("✓ ZeroBus streaming stopped successfully")
            return {'status': 'ok', 'message': 'ZeroBus streaming stopped successfully'}

        except Exception as e:
            logger.error(f"Failed to stop ZeroBus: {e}", exc_info=True)
            return {'status': 'error', 'message': f'Failed to stop ZeroBus: {str(e)}'}

    def get_status(self) -> Dict[str, Any]:
        """Get current status of all components.

        Returns:
            Status dict
        """
        return {
            'active_sources': len(self.clients),
            'zerobus_enabled': self.zerobus_enabled,
            'zerobus_targets': list(self.zerobus_clients.keys()),
            'normalization_enabled': self.normalization_enabled,
            'backpressure_queue_size': self.backpressure.get_metrics().get('queue_size', 0),
            'metrics': self.get_metrics(),
        }
