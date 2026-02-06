"""Factory for creating streaming publishers based on configuration."""

from __future__ import annotations

import logging
from typing import Optional

from .base import StreamPublisher, StreamConfig, StreamTarget

logger = logging.getLogger(__name__)


def create_publisher(config: StreamConfig) -> StreamPublisher:
    """Create appropriate publisher based on target configuration.

    Args:
        config: Streaming configuration specifying target platform

    Returns:
        Initialized publisher instance (not yet connected)

    Raises:
        ValueError: If target is unknown or unsupported
        ImportError: If required dependencies are not installed

    Example:
        >>> config = StreamConfig(
        ...     target=StreamTarget.KAFKA,
        ...     topic_prefix="opcua_bronze",
        ...     protocol="opcua",
        ...     kafka_config={"bootstrap_servers": "localhost:9092"}
        ... )
        >>> publisher = create_publisher(config)
        >>> await publisher.connect()
        >>> await publisher.publish("my_topic", [b"data"])
    """
    if config.target == StreamTarget.KAFKA:
        from .kafka_publisher import KafkaPublisher
        logger.info(f"Creating Kafka publisher for {config.protocol}")
        return KafkaPublisher(config)

    elif config.target == StreamTarget.KINESIS:
        from .kinesis_publisher import KinesisPublisher
        logger.info(f"Creating Kinesis publisher for {config.protocol}")
        return KinesisPublisher(config)

    elif config.target == StreamTarget.ZEROBUS:
        raise NotImplementedError(
            "Zero-Bus publisher not yet implemented. "
            "Use Kafka or Kinesis for now."
        )

    elif config.target == StreamTarget.EVENT_HUBS:
        raise NotImplementedError(
            "Azure Event Hubs publisher not yet implemented. "
            "Consider using Kafka protocol (Event Hubs supports Kafka API)."
        )

    elif config.target == StreamTarget.PUBSUB:
        raise NotImplementedError(
            "Google Pub/Sub publisher not yet implemented."
        )

    else:
        raise ValueError(
            f"Unknown streaming target: {config.target}. "
            f"Supported: {', '.join([t.value for t in StreamTarget])}"
        )


def create_publisher_from_dict(config_dict: dict) -> StreamPublisher:
    """Create publisher from dictionary configuration.

    Args:
        config_dict: Dictionary with keys:
            - target: "kafka" | "kinesis" | "zerobus"
            - topic_prefix: Topic/stream prefix
            - protocol: "opcua" | "mqtt" | "modbus"
            - max_batch_size: Optional batch size (default: 1000)
            - max_batch_wait_ms: Optional batch wait time (default: 5000)
            - compression: Optional compression (default: "snappy")
            - kafka_config: Kafka-specific config (if target=kafka)
            - kinesis_config: Kinesis-specific config (if target=kinesis)

    Returns:
        Initialized publisher instance

    Example:
        >>> config = {
        ...     "target": "kafka",
        ...     "topic_prefix": "opcua_bronze",
        ...     "protocol": "opcua",
        ...     "kafka_config": {
        ...         "bootstrap_servers": "localhost:9092",
        ...         "acks": "all"
        ...     }
        ... }
        >>> publisher = create_publisher_from_dict(config)
    """
    # Convert string target to enum
    target_str = config_dict.get("target")
    if not target_str:
        raise ValueError("'target' is required in config")

    try:
        target = StreamTarget(target_str.lower())
    except ValueError:
        valid_targets = ", ".join([t.value for t in StreamTarget])
        raise ValueError(
            f"Invalid target '{target_str}'. Valid options: {valid_targets}"
        )

    # Build StreamConfig
    config = StreamConfig(
        target=target,
        topic_prefix=config_dict.get("topic_prefix", "ot_data"),
        protocol=config_dict.get("protocol", "opcua"),
        max_batch_size=config_dict.get("max_batch_size", 1000),
        max_batch_wait_ms=config_dict.get("max_batch_wait_ms", 5000),
        compression=config_dict.get("compression", "snappy"),
        kafka_config=config_dict.get("kafka_config"),
        kinesis_config=config_dict.get("kinesis_config"),
        zerobus_config=config_dict.get("zerobus_config"),
    )

    return create_publisher(config)
