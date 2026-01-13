"""Pluggable message parser framework for all protocols.

Allows custom parsers to be registered for different payload formats,
enabling support for proprietary protocols and message structures.

Based on mqtt2uc approach with improvements.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ParsedMessage:
    """Result of message parsing."""
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class MessageParser(ABC):
    """Abstract base class for message parsers."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize parser with configuration.

        Args:
            config: Parser-specific configuration options
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self._stats = {
            "parsed": 0,
            "failed": 0,
            "last_error": None
        }

    @abstractmethod
    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Check if this parser can handle the given data.

        Args:
            raw_data: Raw message bytes
            content_type: Optional content type hint (e.g., "application/json")

        Returns:
            True if this parser can handle the data
        """
        pass

    @abstractmethod
    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Parse raw message data into structured format.

        Args:
            raw_data: Raw message bytes
            context: Optional context information (source, topic, etc.)

        Returns:
            ParsedMessage with parsed data or error
        """
        pass

    def get_stats(self) -> dict[str, Any]:
        """Get parser statistics."""
        return {
            "name": self.name,
            **self._stats
        }

    def _record_success(self):
        """Record successful parse."""
        self._stats["parsed"] += 1

    def _record_failure(self, error: str):
        """Record parse failure."""
        self._stats["failed"] += 1
        self._stats["last_error"] = error


class ChainedParser(MessageParser):
    """Parser that tries multiple parsers in sequence."""

    def __init__(self, parsers: list[MessageParser], config: dict[str, Any] | None = None):
        """Initialize chained parser.

        Args:
            parsers: List of parsers to try in order
            config: Optional configuration
        """
        super().__init__(config)
        self.parsers = parsers

    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Check if any parser in chain can handle data."""
        return any(p.can_parse(raw_data, content_type) for p in self.parsers)

    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Try parsers in sequence until one succeeds."""
        errors = []

        for parser in self.parsers:
            if not parser.can_parse(raw_data):
                continue

            result = parser.parse(raw_data, context)
            if result.success:
                self._record_success()
                return result

            errors.append(f"{parser.name}: {result.error}")

        # All parsers failed
        error_msg = "; ".join(errors) if errors else "No parser could handle data"
        self._record_failure(error_msg)

        return ParsedMessage(
            success=False,
            error=f"Chained parser failed: {error_msg}"
        )


class ParserRegistry:
    """Global registry for message parsers."""

    def __init__(self):
        self._parsers: dict[str, MessageParser] = {}
        self._parser_order: list[str] = []  # Try parsers in registration order

    def register(
        self,
        name: str,
        parser: MessageParser,
        priority: int = 100
    ):
        """Register a parser.

        Args:
            name: Unique parser name
            parser: Parser instance
            priority: Lower numbers = higher priority (tried first)
        """
        if name in self._parsers:
            logger.warning(f"Parser '{name}' already registered, replacing")

        self._parsers[name] = parser
        self._parser_order.append((priority, name))
        self._parser_order.sort()  # Sort by priority

        logger.info(f"Registered parser: {name} (priority={priority})")

    def unregister(self, name: str):
        """Unregister a parser."""
        if name in self._parsers:
            del self._parsers[name]
            self._parser_order = [(p, n) for p, n in self._parser_order if n != name]
            logger.info(f"Unregistered parser: {name}")

    def get_parser(self, name: str) -> MessageParser | None:
        """Get parser by name."""
        return self._parsers.get(name)

    def parse(
        self,
        raw_data: bytes,
        context: dict[str, Any] | None = None,
        parser_hint: str | None = None
    ) -> ParsedMessage:
        """Parse data using registered parsers.

        Args:
            raw_data: Raw message bytes
            context: Optional context information
            parser_hint: Optional parser name to try first

        Returns:
            ParsedMessage with parsed data or error
        """
        # Try hinted parser first
        if parser_hint and parser_hint in self._parsers:
            parser = self._parsers[parser_hint]
            if parser.can_parse(raw_data):
                result = parser.parse(raw_data, context)
                if result.success:
                    return result

        # Try parsers in priority order
        for _, name in self._parser_order:
            parser = self._parsers[name]

            if not parser.can_parse(raw_data):
                continue

            result = parser.parse(raw_data, context)
            if result.success:
                return result

        # No parser could handle data
        return ParsedMessage(
            success=False,
            error=f"No registered parser could handle data (tried {len(self._parsers)} parsers)"
        )

    def get_stats(self) -> dict[str, Any]:
        """Get statistics from all parsers."""
        return {
            name: parser.get_stats()
            for name, parser in self._parsers.items()
        }

    def list_parsers(self) -> list[str]:
        """List all registered parser names."""
        return [name for _, name in self._parser_order]


# Global parser registry instance
_global_registry = ParserRegistry()


def register_parser(name: str, parser: MessageParser, priority: int = 100):
    """Register a parser in the global registry."""
    _global_registry.register(name, parser, priority)


def get_parser(name: str) -> MessageParser | None:
    """Get parser from global registry."""
    return _global_registry.get_parser(name)


def parse_message(
    raw_data: bytes,
    context: dict[str, Any] | None = None,
    parser_hint: str | None = None
) -> ParsedMessage:
    """Parse message using global registry."""
    return _global_registry.parse(raw_data, context, parser_hint)


def get_registry() -> ParserRegistry:
    """Get the global parser registry."""
    return _global_registry


# Decorator for easy parser registration
def parser(name: str, priority: int = 100):
    """Decorator to register a parser class.

    Usage:
        @parser("my_custom_parser", priority=50)
        class MyParser(MessageParser):
            def can_parse(self, raw_data, content_type=None):
                return raw_data.startswith(b"CUSTOM")

            def parse(self, raw_data, context=None):
                # ... parsing logic
                return ParsedMessage(success=True, data={...})
    """
    def decorator(parser_class: type[MessageParser]) -> type[MessageParser]:
        # Instantiate and register
        parser_instance = parser_class()
        register_parser(name, parser_instance, priority)
        return parser_class

    return decorator
