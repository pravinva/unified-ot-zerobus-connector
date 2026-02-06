"""Example: Stream OPC-UA data to AWS Kinesis Data Streams.

This example demonstrates how to:
1. Configure the Kinesis publisher
2. Connect to AWS Kinesis
3. Publish simulated OPC-UA sensor data with partition keys
4. Handle results and sequence numbers

Prerequisites:
    - AWS account with Kinesis stream created
    - AWS credentials configured (IAM role or ~/.aws/credentials)
    - Stream name: ot-data-stream
    - Install dependencies: pip install boto3

Usage:
    python examples/kinesis_streaming_example.py
"""

import asyncio
import logging
from datetime import datetime
from ot_simulator.streaming import create_publisher_from_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function demonstrating Kinesis streaming."""

    # Configuration
    config = {
        "target": "kinesis",
        "topic_prefix": "opcua_bronze",
        "protocol": "opcua",

        "kinesis_config": {
            # Stream configuration
            "stream_name": "ot-data-stream",
            "region_name": "us-east-1",

            # Partitioning strategy: "asset", "protocol", or "random"
            "partition_strategy": "asset",

            # AWS credentials (optional if using IAM role)
            # "aws_access_key_id": "AKIA...",
            # "aws_secret_access_key": "secret...",

            # For LocalStack testing:
            # "endpoint_url": "http://localhost:4566",
        }
    }

    # Create publisher
    logger.info("Creating Kinesis publisher...")
    publisher = create_publisher_from_dict(config)

    try:
        # Connect
        await publisher.connect()
        logger.info("✓ Connected to Kinesis")

        # Generate sample OPC-UA records with partition keys (asset IDs)
        sample_records = []
        partition_keys = []

        assets = ["pump_01", "pump_02", "compressor_01"]
        for i in range(10):
            asset_id = assets[i % len(assets)]

            # Simulate protobuf-serialized record
            record = f"OPC-UA record for {asset_id} at {datetime.now().isoformat()}".encode('utf-8')
            sample_records.append(record)

            # Use asset ID as partition key (groups data by asset in same shard)
            partition_keys.append(asset_id.encode('utf-8'))

        # Publish to Kinesis
        stream_name = config["kinesis_config"]["stream_name"]
        logger.info(f"Publishing {len(sample_records)} records to stream '{stream_name}'...")

        result = await publisher.publish(
            topic=stream_name,  # Kinesis uses stream name (topic param ignored)
            records=sample_records,
            keys=partition_keys  # Asset-based partitioning
        )

        # Check results
        if result.success:
            logger.info(f"✓ Successfully published {result.records_sent} records")

            # Show shard distribution
            shard_ids = [m['shard_id'] for m in result.metadata['sequence_numbers']]
            shard_distribution = {}
            for shard_id in shard_ids:
                shard_distribution[shard_id] = shard_distribution.get(shard_id, 0) + 1

            logger.info(f"  Shard distribution: {shard_distribution}")
            logger.info(f"  Sequence numbers: {result.metadata['sequence_numbers'][:3]}...")

        else:
            logger.error(f"✗ Failed to publish {result.records_failed} records")
            logger.error(f"  Error: {result.error}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

    finally:
        # Cleanup
        await publisher.close()
        logger.info("✓ Closed Kinesis publisher")


if __name__ == "__main__":
    asyncio.run(main())
