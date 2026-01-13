"""Pluggable message parser framework.

Provides extensible message parsing for all protocols with built-in
support for JSON, Sparkplug B, CSV, binary formats, and more.
"""
from opcua2uc.parsers.base import (
    MessageParser,
    ParsedMessage,
    ChainedParser,
    ParserRegistry,
    register_parser,
    get_parser,
    parse_message,
    get_registry,
    parser,
)

# Import built-in parsers to auto-register them
from opcua2uc.parsers import builtin

__all__ = [
    "MessageParser",
    "ParsedMessage",
    "ChainedParser",
    "ParserRegistry",
    "register_parser",
    "get_parser",
    "parse_message",
    "get_registry",
    "parser",
]
