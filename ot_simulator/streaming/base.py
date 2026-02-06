"""Abstract base classes for streaming connectors.

Provides common interface for Kafka, Kinesis, and Zero-Bus publishers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum


class StreamTarget(str, Enum):
    """Supported streaming targets."""

    KAFKA = "kafka"
    KINESIS = "kinesis"
    ZEROBUS = "zerobus"
    EVENT_HUBS = "event_hubs"  # Future: Azure Event Hubs
    PUBSUB = "pubsub"  # Future: Google Pub/Sub


@dataclass
class StreamConfig:
    """Configuration for streaming publisher.

    Attributes:
        target: Which streaming platform to use
        topic_prefix: Prefix for topic/stream names (e.g., "opcua_bronze")
        protocol: Source protocol (opcua, mqtt, modbus)
        max_batch_size: Maximum records per batch
        max_batch_wait_ms: Maximum time to wait before flushing batch
        compression: Compression codec (gzip, snappy, lz4, zstd, none)
        **target_specific: Target-specific configuration
    """

    target: StreamTarget
    topic_prefix: str
    protocol: str
    max_batch_size: int = 1000
    max_batch_wait_ms: int = 5000
    compression: str = "snappy"

    # Target-specific config (passed as kwargs)
    kafka_config: Optional[dict[str, Any]] = None
    kinesis_config: Optional[dict[str, Any]] = None
    zerobus_config: Optional[dict[str, Any]] = None


@dataclass
class PublishResult:
    """Result of publishing records.

    Attributes:
        success: Whether all records were published successfully
        records_sent: Number of records successfully published
        records_failed: Number of records that failed
        error: Error message if any
        metadata: Target-specific metadata (offsets, sequence numbers, etc.)
    """

    success: bool
    records_sent: int
    records_failed: int = 0
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class StreamPublisher(ABC):
    """Abstract base class for streaming publishers.

    All streaming connectors (Kafka, Kinesis, Zero-Bus) implement this interface.
    """

    def __init__(self, config: StreamConfig):
        """Initialize publisher with configuration.

        Args:
            config: Streaming configuration
        """
        self.config = config
        self._connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to streaming platform.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def publish(
        self,
        topic: str,
        records: list[bytes],
        keys: Optional[list[Optional[bytes]]] = None
    ) -> PublishResult:
        """Publish records to the streaming platform.

        Args:
            topic: Topic/stream name to publish to
            records: List of serialized records (protobuf bytes)
            keys: Optional list of keys for partitioning (same length as records)

        Returns:
            PublishResult with success status and metadata

        Raises:
            RuntimeError: If not connected
            PublishError: If publishing fails
        """
        pass

    @abstractmethod
    async def flush(self) -> None:
        """Flush any pending records.

        Blocks until all records are sent or timeout occurs.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection and cleanup resources."""
        pass

    @property
    def is_connected(self) -> bool:
        """Check if publisher is connected."""
        return self._connected

    def get_topic_name(self, suffix: str = "") -> str:
        """Generate topic name with prefix.

        Args:
            suffix: Optional suffix to append (e.g., "_dlq" for dead letter queue)

        Returns:
            Full topic name: <prefix>_<protocol><suffix>

        Example:
            >>> publisher.get_topic_name()
            'opcua_bronze_opcua'
            >>> publisher.get_topic_name('_dlq')
            'opcua_bronze_opcua_dlq'
        """
        base = f"{self.config.topic_prefix}_{self.config.protocol}"
        return f"{base}{suffix}" if suffix else base
