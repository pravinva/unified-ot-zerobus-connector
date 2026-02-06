"""Example: Stream OPC-UA data to Apache Kafka.

This example demonstrates how to:
1. Configure the Kafka publisher
2. Connect to a Kafka cluster
3. Publish simulated OPC-UA sensor data
4. Handle results and errors

Prerequisites:
    - Kafka cluster running (or use Confluent Cloud)
    - Topic created: opcua_bronze_opcua
    - Install dependencies: pip install aiokafka

Usage:
    python examples/kafka_streaming_example.py
"""

import asyncio
import logging
from datetime import datetime
from ot_simulator.streaming import create_publisher_from_dict, StreamTarget

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function demonstrating Kafka streaming."""

    # Configuration
    config = {
        "target": "kafka",
        "topic_prefix": "opcua_bronze",
        "protocol": "opcua",
        "compression": "snappy",
        "max_batch_size": 1000,

        "kafka_config": {
            # Connection
            "bootstrap_servers": "localhost:9092",

            # Delivery guarantees
            "acks": "all",  # Wait for all replicas (durability)
            "enable_idempotence": True,  # Exactly-once semantics

            # Security (uncomment for production)
            # "security_protocol": "SASL_SSL",
            # "sasl_mechanism": "SCRAM-SHA-512",
            # "sasl_username": "your-username",
            # "sasl_password": "your-password",
        }
    }

    # Create publisher
    logger.info("Creating Kafka publisher...")
    publisher = create_publisher_from_dict(config)

    try:
        # Connect
        await publisher.connect()
        logger.info("✓ Connected to Kafka")

        # Generate sample OPC-UA records (in real usage, these come from OPC-UA server)
        sample_records = []
        for i in range(10):
            # Simulate protobuf-serialized record
            record = f"OPC-UA record {i} at {datetime.now().isoformat()}".encode('utf-8')
            sample_records.append(record)

        # Publish to Kafka
        topic = publisher.get_topic_name()  # "opcua_bronze_opcua"
        logger.info(f"Publishing {len(sample_records)} records to topic '{topic}'...")

        result = await publisher.publish(
            topic=topic,
            records=sample_records
        )

        # Check results
        if result.success:
            logger.info(f"✓ Successfully published {result.records_sent} records")
            logger.info(f"  Offsets: {result.metadata['offsets'][:3]}...")  # Show first 3
        else:
            logger.error(f"✗ Failed to publish {result.records_failed} records")
            logger.error(f"  Error: {result.error}")

        # Flush any remaining buffered records
        await publisher.flush()
        logger.info("✓ Flushed producer buffer")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

    finally:
        # Cleanup
        await publisher.close()
        logger.info("✓ Closed Kafka publisher")


if __name__ == "__main__":
    asyncio.run(main())
