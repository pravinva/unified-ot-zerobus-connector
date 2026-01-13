"""Protobuf schema generator from Unity Catalog tables.

Generates .proto files from Databricks Unity Catalog table schemas for
efficient binary serialization and message parsing.

Based on mqtt2uc approach: https://github.com/bachwehbi/mqtt2uc
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProtoField:
    """Represents a field in a Protobuf message."""
    name: str
    proto_type: str
    field_number: int
    repeated: bool = False
    optional: bool = False
    comment: str = ""


@dataclass
class ProtoMessage:
    """Represents a Protobuf message definition."""
    name: str
    fields: list[ProtoField]
    comment: str = ""


class ProtobufGenerator:
    """Generate Protobuf schemas from Unity Catalog tables."""

    # Unity Catalog type to Protobuf type mapping
    UC_TO_PROTO_TYPE_MAP = {
        # Numeric types
        "BOOLEAN": "bool",
        "TINYINT": "int32",
        "SMALLINT": "int32",
        "INT": "int32",
        "INTEGER": "int32",
        "BIGINT": "int64",
        "LONG": "int64",
        "FLOAT": "float",
        "DOUBLE": "double",
        "DECIMAL": "double",  # Note: Protobuf doesn't have decimal, use double

        # String types
        "STRING": "string",
        "VARCHAR": "string",
        "CHAR": "string",

        # Binary
        "BINARY": "bytes",

        # Date/Time
        "DATE": "string",  # ISO 8601 format
        "TIMESTAMP": "int64",  # Unix timestamp in milliseconds
        "TIMESTAMP_NTZ": "int64",  # Unix timestamp

        # Complex types (handled specially)
        "ARRAY": None,  # Will use repeated
        "STRUCT": None,  # Will create nested message
        "MAP": None,  # Will create nested message with key/value
    }

    def __init__(self):
        self.generated_messages: dict[str, ProtoMessage] = {}
        self.field_counter = 1

    def generate_from_table_schema(
        self,
        table_schema: list[dict[str, Any]],
        message_name: str,
        package_name: str = "iot.databricks"
    ) -> str:
        """Generate Protobuf schema from Unity Catalog table schema.

        Args:
            table_schema: List of column definitions from UC table
                Format: [{"name": "col1", "type": "STRING", "nullable": True, "comment": "..."}]
            message_name: Name for the Protobuf message
            package_name: Protobuf package name

        Returns:
            Complete .proto file content as string
        """
        self.generated_messages = {}
        self.field_counter = 1

        # Generate main message
        fields = self._generate_fields_from_schema(table_schema)
        main_message = ProtoMessage(
            name=message_name,
            fields=fields,
            comment=f"Generated from Unity Catalog table schema"
        )
        self.generated_messages[message_name] = main_message

        # Build .proto file
        proto_content = self._build_proto_file(package_name)
        return proto_content

    def _generate_fields_from_schema(
        self,
        schema: list[dict[str, Any]],
        field_number_start: int = 1
    ) -> list[ProtoField]:
        """Generate Protobuf fields from schema columns."""
        fields = []
        field_number = field_number_start

        for column in schema:
            name = column["name"]
            uc_type = column["type"].upper()
            nullable = column.get("nullable", True)
            comment = column.get("comment", "")

            # Handle complex types
            if uc_type.startswith("ARRAY<"):
                # Extract element type
                element_type = uc_type[6:-1]  # Remove "ARRAY<" and ">"
                proto_type = self._map_uc_type_to_proto(element_type)

                fields.append(ProtoField(
                    name=name,
                    proto_type=proto_type,
                    field_number=field_number,
                    repeated=True,
                    optional=False,
                    comment=comment
                ))

            elif uc_type.startswith("STRUCT<"):
                # Create nested message for struct
                nested_message_name = f"{name.capitalize()}Struct"
                struct_fields = self._parse_struct_type(uc_type)
                nested_message = ProtoMessage(
                    name=nested_message_name,
                    fields=struct_fields,
                    comment=f"Nested struct for {name}"
                )
                self.generated_messages[nested_message_name] = nested_message

                fields.append(ProtoField(
                    name=name,
                    proto_type=nested_message_name,
                    field_number=field_number,
                    optional=nullable,
                    comment=comment
                ))

            elif uc_type.startswith("MAP<"):
                # Create nested message for map entry
                map_message_name = f"{name.capitalize()}Entry"
                key_type, value_type = self._parse_map_type(uc_type)
                map_fields = [
                    ProtoField("key", key_type, 1),
                    ProtoField("value", value_type, 2)
                ]
                map_message = ProtoMessage(
                    name=map_message_name,
                    fields=map_fields,
                    comment=f"Map entry for {name}"
                )
                self.generated_messages[map_message_name] = map_message

                fields.append(ProtoField(
                    name=name,
                    proto_type=map_message_name,
                    field_number=field_number,
                    repeated=True,
                    comment=comment
                ))

            else:
                # Simple type
                proto_type = self._map_uc_type_to_proto(uc_type)
                fields.append(ProtoField(
                    name=name,
                    proto_type=proto_type,
                    field_number=field_number,
                    optional=nullable,
                    comment=comment
                ))

            field_number += 1

        return fields

    def _map_uc_type_to_proto(self, uc_type: str) -> str:
        """Map Unity Catalog type to Protobuf type."""
        # Remove precision/scale for DECIMAL
        if uc_type.startswith("DECIMAL"):
            return "double"

        base_type = uc_type.split("(")[0].upper()
        proto_type = self.UC_TO_PROTO_TYPE_MAP.get(base_type)

        if proto_type is None:
            logger.warning(f"Unknown UC type: {uc_type}, defaulting to string")
            return "string"

        return proto_type

    def _parse_struct_type(self, struct_type: str) -> list[ProtoField]:
        """Parse STRUCT<field1:type1,field2:type2> into fields."""
        # Simplified parser - real implementation needs better parsing
        inner = struct_type[7:-1]  # Remove "STRUCT<" and ">"

        fields = []
        field_number = 1

        # Split by comma (simplified - doesn't handle nested commas)
        parts = inner.split(",")

        for part in parts:
            if ":" in part:
                field_name, field_type = part.strip().split(":", 1)
                proto_type = self._map_uc_type_to_proto(field_type.strip())
                fields.append(ProtoField(
                    name=field_name.strip(),
                    proto_type=proto_type,
                    field_number=field_number
                ))
                field_number += 1

        return fields

    def _parse_map_type(self, map_type: str) -> tuple[str, str]:
        """Parse MAP<key_type,value_type> into key and value types."""
        inner = map_type[4:-1]  # Remove "MAP<" and ">"
        key_type, value_type = inner.split(",", 1)

        proto_key_type = self._map_uc_type_to_proto(key_type.strip())
        proto_value_type = self._map_uc_type_to_proto(value_type.strip())

        return proto_key_type, proto_value_type

    def _build_proto_file(self, package_name: str) -> str:
        """Build complete .proto file content."""
        lines = [
            'syntax = "proto3";',
            "",
            f"package {package_name};",
            "",
            "// Auto-generated from Unity Catalog table schema",
            "// Do not edit manually",
            "",
        ]

        # Add all messages
        for message_name, message in self.generated_messages.items():
            lines.extend(self._build_message_definition(message))
            lines.append("")

        return "\n".join(lines)

    def _build_message_definition(self, message: ProtoMessage) -> list[str]:
        """Build Protobuf message definition."""
        lines = []

        # Message comment
        if message.comment:
            lines.append(f"// {message.comment}")

        lines.append(f"message {message.name} {{")

        # Fields
        for field in message.fields:
            # Field comment
            if field.comment:
                lines.append(f"  // {field.comment}")

            # Build field line
            field_line = "  "

            if field.optional:
                field_line += "optional "

            if field.repeated:
                field_line += "repeated "

            field_line += f"{field.proto_type} {field.name} = {field.field_number};"

            lines.append(field_line)

        lines.append("}")

        return lines

    def save_to_file(self, proto_content: str, output_path: Path | str):
        """Save generated Protobuf schema to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            f.write(proto_content)

        logger.info(f"Generated Protobuf schema saved to {output_path}")


def generate_proto_from_databricks_table(
    workspace_client: Any,
    catalog: str,
    schema: str,
    table: str,
    output_path: Path | str | None = None,
    message_name: str | None = None,
    package_name: str = "iot.databricks"
) -> str:
    """Generate Protobuf schema from Databricks Unity Catalog table.

    Args:
        workspace_client: Databricks WorkspaceClient instance
        catalog: UC catalog name
        schema: UC schema name
        table: UC table name
        output_path: Optional path to save .proto file
        message_name: Optional custom message name (defaults to table name)
        package_name: Protobuf package name

    Returns:
        Generated .proto file content
    """
    # Get table metadata
    full_table_name = f"{catalog}.{schema}.{table}"
    table_info = workspace_client.tables.get(full_table_name)

    # Extract column schema
    columns = []
    for col in table_info.columns:
        columns.append({
            "name": col.name,
            "type": col.type_text,
            "nullable": col.nullable,
            "comment": col.comment or ""
        })

    # Generate message name from table if not provided
    if message_name is None:
        # Convert table name to PascalCase
        message_name = "".join(word.capitalize() for word in table.split("_"))

    # Generate Protobuf schema
    generator = ProtobufGenerator()
    proto_content = generator.generate_from_table_schema(
        table_schema=columns,
        message_name=message_name,
        package_name=package_name
    )

    # Save to file if path provided
    if output_path:
        generator.save_to_file(proto_content, output_path)

    return proto_content


# Example usage
if __name__ == "__main__":
    # Example table schema (as if from Unity Catalog)
    example_schema = [
        {"name": "event_time_ms", "type": "BIGINT", "nullable": False, "comment": "Event timestamp in milliseconds"},
        {"name": "source_name", "type": "STRING", "nullable": False, "comment": "Data source identifier"},
        {"name": "sensor_path", "type": "STRING", "nullable": False, "comment": "Sensor path or topic"},
        {"name": "value", "type": "DOUBLE", "nullable": True, "comment": "Numeric sensor value"},
        {"name": "value_string", "type": "STRING", "nullable": True, "comment": "String sensor value"},
        {"name": "status", "type": "STRING", "nullable": True, "comment": "Sensor status"},
        {"name": "metadata", "type": "STRUCT<unit:STRING,type:STRING,min:DOUBLE,max:DOUBLE>", "nullable": True, "comment": "Sensor metadata"},
        {"name": "tags", "type": "ARRAY<STRING>", "nullable": True, "comment": "Custom tags"},
    ]

    generator = ProtobufGenerator()
    proto = generator.generate_from_table_schema(
        table_schema=example_schema,
        message_name="SensorEvent",
        package_name="iot.databricks"
    )

    print(proto)
    print("\n# Generated Protobuf schema successfully!")
