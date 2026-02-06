"""Streaming connector abstraction for multiple targets (Kafka, Kinesis, Zero-Bus).

This module provides a unified interface for publishing OT data to various streaming platforms.
"""

from __future__ import annotations

from .base import StreamPublisher, StreamConfig, PublishResult
from .factory import create_publisher

__all__ = [
    "StreamPublisher",
    "StreamConfig",
    "PublishResult",
    "create_publisher",
]
