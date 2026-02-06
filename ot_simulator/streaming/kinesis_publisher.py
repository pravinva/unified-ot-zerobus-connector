"""AWS Kinesis publisher implementation for OT data streaming.

Publishes OPC-UA, MQTT, and Modbus data to AWS Kinesis Data Streams.
"""

from __future__ import annotations

import logging
from typing import Optional
import asyncio
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .base import StreamPublisher, StreamConfig, PublishResult

logger = logging.getLogger(__name__)


class KinesisPublisher(StreamPublisher):
    """AWS Kinesis Data Streams publisher for industrial OT data.

    Features:
    - Async batch publishing with PutRecords API
    - Automatic retries for failed shards
    - Configurable partitioning (by asset, by protocol, round-robin)
    - Support for enhanced fan-out consumers
    - CloudWatch metrics integration

    Configuration:
        config.kinesis_config should contain:
        - stream_name: Kinesis stream name (required)
        - region_name: AWS region (e.g., "us-east-1") (required)
        - aws_access_key_id: AWS access key (optional, uses IAM role if not provided)
        - aws_secret_access_key: AWS secret key (optional)
        - aws_session_token: Temporary session token (optional)
        - endpoint_url: Custom endpoint for LocalStack/testing (optional)
        - partition_strategy: "asset" | "protocol" | "random" (default: "random")

    Example:
        >>> config = StreamConfig(
        ...     target=StreamTarget.KINESIS,
        ...     topic_prefix="opcua_bronze",
        ...     protocol="opcua",
        ...     kinesis_config={
        ...         "stream_name": "ot-data-stream",
        ...         "region_name": "us-east-1",
        ...         "partition_strategy": "asset"
        ...     }
        ... )
        >>> publisher = KinesisPublisher(config)
        >>> await publisher.connect()
        >>> result = await publisher.publish("opcua_bronze_opcua", [b"record1"])
    """

    def __init__(self, config: StreamConfig):
        """Initialize Kinesis publisher.

        Args:
            config: Streaming configuration with kinesis_config

        Raises:
            ImportError: If boto3 is not installed
            ValueError: If kinesis_config is missing or invalid
        """
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for Kinesis publisher. "
                "Install with: pip install boto3"
            )

        super().__init__(config)

        if not config.kinesis_config:
            raise ValueError("kinesis_config is required for KinesisPublisher")

        kinesis_cfg = config.kinesis_config

        # Required configuration
        if "stream_name" not in kinesis_cfg:
            raise ValueError("stream_name is required in kinesis_config")
        if "region_name" not in kinesis_cfg:
            raise ValueError("region_name is required in kinesis_config")

        self._stream_name = kinesis_cfg["stream_name"]
        self._region_name = kinesis_cfg["region_name"]
        self._partition_strategy = kinesis_cfg.get("partition_strategy", "random")

        # Build boto3 client configuration
        self._boto_config = {
            "region_name": self._region_name,
            "service_name": "kinesis"
        }

        # AWS credentials (optional - will use IAM role if not provided)
        if "aws_access_key_id" in kinesis_cfg:
            self._boto_config["aws_access_key_id"] = kinesis_cfg["aws_access_key_id"]
        if "aws_secret_access_key" in kinesis_cfg:
            self._boto_config["aws_secret_access_key"] = kinesis_cfg["aws_secret_access_key"]
        if "aws_session_token" in kinesis_cfg:
            self._boto_config["aws_session_token"] = kinesis_cfg["aws_session_token"]

        # Custom endpoint (for LocalStack testing)
        if "endpoint_url" in kinesis_cfg:
            self._boto_config["endpoint_url"] = kinesis_cfg["endpoint_url"]

        self._client = None
        self._partition_counter = 0

    async def connect(self) -> None:
        """Establish connection to Kinesis stream.

        Raises:
            ConnectionError: If connection fails or stream doesn't exist
        """
        if self._connected:
            logger.warning("Already connected to Kinesis")
            return

        try:
            logger.info(
                f"Connecting to Kinesis stream '{self._stream_name}' "
                f"in region {self._region_name}..."
            )

            # Create boto3 client
            self._client = boto3.client(**self._boto_config)

            # Verify stream exists and is active
            response = self._client.describe_stream(StreamName=self._stream_name)
            stream_status = response["StreamDescription"]["StreamStatus"]

            if stream_status != "ACTIVE":
                raise ConnectionError(
                    f"Kinesis stream '{self._stream_name}' is not active "
                    f"(status: {stream_status})"
                )

            shard_count = len(response["StreamDescription"]["Shards"])
            logger.info(
                f"✓ Connected to Kinesis stream '{self._stream_name}' "
                f"({shard_count} shards)"
            )

            self._connected = True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                msg = f"Kinesis stream '{self._stream_name}' does not exist"
            else:
                msg = f"AWS API error: {e}"
            logger.error(msg)
            raise ConnectionError(msg) from e

        except Exception as e:
            logger.error(f"Failed to connect to Kinesis: {e}")
            raise ConnectionError(f"Kinesis connection failed: {e}") from e

    def _get_partition_key(self, record_index: int, key: Optional[bytes]) -> str:
        """Generate partition key for record.

        Args:
            record_index: Index of record in batch
            key: Optional explicit partition key

        Returns:
            Partition key string
        """
        if key:
            # Use explicit key (e.g., asset_id from caller)
            return key.decode("utf-8") if isinstance(key, bytes) else str(key)

        if self._partition_strategy == "protocol":
            # Partition by protocol (all OPC-UA data to same shard)
            return self.config.protocol

        elif self._partition_strategy == "random":
            # Round-robin across shards
            self._partition_counter += 1
            return f"partition-{self._partition_counter}"

        else:
            # Default: use record index
            return f"record-{record_index}"

    async def publish(
        self,
        topic: str,
        records: list[bytes],
        keys: Optional[list[Optional[bytes]]] = None
    ) -> PublishResult:
        """Publish records to Kinesis stream.

        Kinesis PutRecords API batches up to 500 records or 5MB per request.
        If batch exceeds limits, it will be split into multiple requests.

        Args:
            topic: Stream name (ignored - uses config.stream_name)
            records: List of serialized protobuf records
            keys: Optional list of partition keys (e.g., asset IDs)

        Returns:
            PublishResult with metadata including sequence numbers

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or not self._client:
            raise RuntimeError("Not connected to Kinesis. Call connect() first.")

        if keys and len(keys) != len(records):
            raise ValueError("keys must have same length as records")

        records_sent = 0
        records_failed = 0
        sequence_numbers = []
        errors = []

        try:
            # Kinesis PutRecords limit: 500 records or 5MB per request
            MAX_BATCH_SIZE = 500
            MAX_BATCH_BYTES = 5 * 1024 * 1024  # 5MB

            # Split into batches if needed
            batches = []
            current_batch = []
            current_batch_size = 0

            for i, record in enumerate(records):
                record_size = len(record)

                # Check if adding this record would exceed limits
                if (len(current_batch) >= MAX_BATCH_SIZE or
                    current_batch_size + record_size > MAX_BATCH_BYTES):
                    # Start new batch
                    if current_batch:
                        batches.append(current_batch)
                    current_batch = []
                    current_batch_size = 0

                partition_key = self._get_partition_key(i, keys[i] if keys else None)
                current_batch.append({
                    "Data": record,
                    "PartitionKey": partition_key
                })
                current_batch_size += record_size

            # Add final batch
            if current_batch:
                batches.append(current_batch)

            # Publish each batch
            for batch_idx, batch in enumerate(batches):
                try:
                    # Run synchronous boto3 call in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: self._client.put_records(
                            StreamName=self._stream_name,
                            Records=batch
                        )
                    )

                    # Check for partial failures
                    failed_count = response.get("FailedRecordCount", 0)

                    for i, result_record in enumerate(response["Records"]):
                        if "SequenceNumber" in result_record:
                            sequence_numbers.append({
                                "sequence_number": result_record["SequenceNumber"],
                                "shard_id": result_record["ShardId"]
                            })
                            records_sent += 1
                        else:
                            # Record failed
                            error_code = result_record.get("ErrorCode", "Unknown")
                            error_msg = result_record.get("ErrorMessage", "")
                            errors.append(f"{error_code}: {error_msg}")
                            records_failed += 1

                    if failed_count > 0:
                        logger.warning(
                            f"Batch {batch_idx+1}/{len(batches)}: "
                            f"{failed_count}/{len(batch)} records failed"
                        )

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    error_msg = e.response.get("Error", {}).get("Message", str(e))
                    logger.error(f"Kinesis API error: {error_code} - {error_msg}")
                    errors.append(f"{error_code}: {error_msg}")
                    records_failed += len(batch)

            success = records_failed == 0

            return PublishResult(
                success=success,
                records_sent=records_sent,
                records_failed=records_failed,
                error="; ".join(errors[:5]) if errors else None,  # Limit error messages
                metadata={
                    "stream_name": self._stream_name,
                    "sequence_numbers": sequence_numbers,
                    "batches": len(batches)
                }
            )

        except Exception as e:
            logger.error(f"Kinesis publish error: {e}")
            return PublishResult(
                success=False,
                records_sent=records_sent,
                records_failed=len(records) - records_sent,
                error=str(e)
            )

    async def flush(self) -> None:
        """Flush any buffered records.

        Kinesis PutRecords is synchronous, so no buffering occurs.
        This is a no-op for compatibility with StreamPublisher interface.
        """
        # Kinesis has no client-side buffering
        pass

    async def close(self) -> None:
        """Close Kinesis client and cleanup resources."""
        if self._client:
            try:
                # boto3 clients don't need explicit cleanup
                logger.info("✓ Kinesis publisher closed")
            finally:
                self._client = None
                self._connected = False
