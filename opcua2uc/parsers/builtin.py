"""Built-in message parsers for common formats.

Provides parsers for JSON, Sparkplug B, raw binary, and other common formats.
"""
from __future__ import annotations

import json
import logging
import struct
from typing import Any

from opcua2uc.parsers.base import MessageParser, ParsedMessage, parser

logger = logging.getLogger(__name__)


@parser("json", priority=10)
class JSONParser(MessageParser):
    """Parse JSON payloads."""

    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Check if data is JSON."""
        if content_type and "json" in content_type.lower():
            return True

        # Try to detect JSON by first character
        if not raw_data:
            return False

        first_char = raw_data[0:1]
        return first_char in (b"{", b"[")

    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Parse JSON data."""
        try:
            data = json.loads(raw_data.decode("utf-8"))
            self._record_success()

            return ParsedMessage(
                success=True,
                data=data,
                metadata={"format": "json", "size": len(raw_data)}
            )

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            error = f"JSON parse error: {e}"
            self._record_failure(error)
            return ParsedMessage(success=False, error=error)


@parser("string", priority=90)
class StringParser(MessageParser):
    """Parse plain text/string payloads."""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.encoding = self.config.get("encoding", "utf-8")

    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Always returns True as fallback parser."""
        return True

    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Parse as UTF-8 string."""
        try:
            text = raw_data.decode(self.encoding)
            self._record_success()

            # Try to convert to number if possible
            value: Any = text
            try:
                if "." in text:
                    value = float(text)
                else:
                    value = int(text)
            except (ValueError, AttributeError):
                pass  # Keep as string

            return ParsedMessage(
                success=True,
                data={"value": value, "raw_text": text},
                metadata={"format": "string", "encoding": self.encoding}
            )

        except UnicodeDecodeError as e:
            error = f"String decode error: {e}"
            self._record_failure(error)
            return ParsedMessage(success=False, error=error)


@parser("sparkplug_b", priority=20)
class SparkplugBParser(MessageParser):
    """Parse Sparkplug B payloads (simplified JSON format).

    Full Sparkplug B uses Protobuf, but many implementations use JSON.
    """

    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Check if data looks like Sparkplug B."""
        if not raw_data or not raw_data.startswith(b"{"):
            return False

        try:
            data = json.loads(raw_data.decode("utf-8"))
            # Sparkplug B has "timestamp" and "metrics" fields
            return isinstance(data, dict) and "metrics" in data

        except (json.JSONDecodeError, UnicodeDecodeError):
            return False

    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Parse Sparkplug B data."""
        try:
            data = json.loads(raw_data.decode("utf-8"))

            # Extract metrics
            timestamp = data.get("timestamp")
            metrics = data.get("metrics", [])

            # Flatten metrics into dict
            values = {}
            for metric in metrics:
                name = metric.get("name")
                value = metric.get("value")
                if name and value is not None:
                    values[name] = value

            self._record_success()

            return ParsedMessage(
                success=True,
                data={
                    "timestamp": timestamp,
                    "values": values,
                    "raw_metrics": metrics
                },
                metadata={"format": "sparkplug_b", "metric_count": len(metrics)}
            )

        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
            error = f"Sparkplug B parse error: {e}"
            self._record_failure(error)
            return ParsedMessage(success=False, error=error)


@parser("binary_struct", priority=30)
class BinaryStructParser(MessageParser):
    """Parse binary data using struct format.

    Config:
        format: struct format string (e.g., "!HHf" for 2 uint16 + 1 float)
        fields: list of field names
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.format = self.config.get("format", "")
        self.fields = self.config.get("fields", [])
        self.expected_size = struct.calcsize(self.format) if self.format else 0

    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Check if data matches expected binary format."""
        if not self.format or not self.expected_size:
            return False

        return len(raw_data) == self.expected_size

    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Parse binary struct data."""
        try:
            values = struct.unpack(self.format, raw_data)

            # Map to field names if provided
            if self.fields and len(self.fields) == len(values):
                data = dict(zip(self.fields, values))
            else:
                data = {"values": values}

            self._record_success()

            return ParsedMessage(
                success=True,
                data=data,
                metadata={"format": "binary_struct", "struct_format": self.format}
            )

        except struct.error as e:
            error = f"Binary struct parse error: {e}"
            self._record_failure(error)
            return ParsedMessage(success=False, error=error)


@parser("csv", priority=40)
class CSVParser(MessageParser):
    """Parse CSV-formatted payloads.

    Config:
        delimiter: field delimiter (default: ",")
        has_header: whether first line is header (default: False)
        fields: list of field names if no header
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.delimiter = self.config.get("delimiter", ",")
        self.has_header = self.config.get("has_header", False)
        self.fields = self.config.get("fields", [])

    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Check if data looks like CSV."""
        if content_type and "csv" in content_type.lower():
            return True

        try:
            text = raw_data.decode("utf-8")
            # Simple heuristic: contains delimiter and no JSON/XML markers
            return self.delimiter in text and not text.strip().startswith(("{", "<"))
        except UnicodeDecodeError:
            return False

    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Parse CSV data."""
        try:
            text = raw_data.decode("utf-8")
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            if not lines:
                return ParsedMessage(success=False, error="Empty CSV data")

            # Handle header
            if self.has_header:
                header = lines[0].split(self.delimiter)
                data_lines = lines[1:]
            else:
                header = self.fields or [f"field_{i}" for i in range(len(lines[0].split(self.delimiter)))]
                data_lines = lines

            # Parse rows
            rows = []
            for line in data_lines:
                values = line.split(self.delimiter)
                row = {}
                for i, value in enumerate(values):
                    if i < len(header):
                        # Try to convert to number
                        try:
                            if "." in value:
                                row[header[i]] = float(value)
                            else:
                                row[header[i]] = int(value)
                        except ValueError:
                            row[header[i]] = value
                rows.append(row)

            self._record_success()

            return ParsedMessage(
                success=True,
                data={"rows": rows, "count": len(rows)},
                metadata={"format": "csv", "delimiter": self.delimiter}
            )

        except (UnicodeDecodeError, ValueError) as e:
            error = f"CSV parse error: {e}"
            self._record_failure(error)
            return ParsedMessage(success=False, error=error)


@parser("modbus_registers", priority=50)
class ModbusRegisterParser(MessageParser):
    """Parse Modbus register values.

    Config:
        scale_factor: divide values by this (default: 1)
        registers: list of register definitions
            [{"name": "temp", "offset": 0, "type": "int16"}]
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.scale_factor = self.config.get("scale_factor", 1)
        self.registers = self.config.get("registers", [])

    def can_parse(self, raw_data: bytes, content_type: str | None = None) -> bool:
        """Check if data is modbus registers."""
        # Must be even number of bytes (16-bit registers)
        return len(raw_data) % 2 == 0

    def parse(self, raw_data: bytes, context: dict[str, Any] | None = None) -> ParsedMessage:
        """Parse Modbus register data."""
        try:
            # Unpack as 16-bit big-endian signed integers
            register_count = len(raw_data) // 2
            values = struct.unpack(f">{register_count}h", raw_data)

            # Apply scaling
            scaled_values = [v / self.scale_factor for v in values]

            # Map to register names if configured
            data = {}
            if self.registers:
                for reg_def in self.registers:
                    name = reg_def.get("name")
                    offset = reg_def.get("offset", 0)
                    if 0 <= offset < len(scaled_values):
                        data[name] = scaled_values[offset]
            else:
                data = {"registers": scaled_values}

            self._record_success()

            return ParsedMessage(
                success=True,
                data=data,
                metadata={
                    "format": "modbus_registers",
                    "register_count": register_count,
                    "scale_factor": self.scale_factor
                }
            )

        except struct.error as e:
            error = f"Modbus register parse error: {e}"
            self._record_failure(error)
            return ParsedMessage(success=False, error=error)


# Initialize all built-in parsers on module import
def init_builtin_parsers():
    """Initialize all built-in parsers.

    This is called automatically on module import due to @parser decorators.
    """
    logger.info("Built-in parsers initialized")


# Auto-init on import
init_builtin_parsers()
