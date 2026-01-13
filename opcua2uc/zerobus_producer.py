from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from zerobus.sdk.aio import ZerobusSdk
from zerobus.sdk.shared import RecordType, StreamConfigurationOptions, TableProperties


class ZerobusConfigError(RuntimeError):
    pass


def _utc_now_us() -> int:
    # UC TIMESTAMP columns: Zerobus JSON ingestion expects epoch microseconds.
    return int(datetime.now(timezone.utc).timestamp() * 1_000_000)


def _read_env_var_name(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ZerobusConfigError(f"Missing databricks.auth.{key}")
    return v.strip()


def _require_str(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ZerobusConfigError(f"Missing databricks.{key}")
    return v.strip()


def _target_table_name(databricks_cfg: dict[str, Any]) -> str:
    target = databricks_cfg.get("target")
    if not isinstance(target, dict):
        raise ZerobusConfigError("Missing databricks.target")

    catalog = target.get("catalog")
    schema = target.get("schema")
    table = target.get("table")
    for k, v in ("catalog", catalog), ("schema", schema), ("table", table):
        if not isinstance(v, str) or not v.strip():
            raise ZerobusConfigError(f"Missing databricks.target.{k}")

    return f"{catalog.strip()}.{schema.strip()}.{table.strip()}"


@dataclass
class ZerobusTestResult:
    table_name: str
    stream_id: str


async def zerobus_test_ingest(databricks_cfg: dict[str, Any], record: dict[str, Any]) -> ZerobusTestResult:
    """Write exactly one JSON record through Zerobus and wait for durability."""

    # The SDK's OAuth token request is sensitive to trailing slashes.
    workspace_host = _require_str(databricks_cfg, "workspace_host").rstrip("/")
    zerobus_endpoint = _require_str(databricks_cfg, "zerobus_endpoint")
    table_name = _target_table_name(databricks_cfg)

    auth_cfg = databricks_cfg.get("auth")
    if not isinstance(auth_cfg, dict):
        raise ZerobusConfigError("Missing databricks.auth")

    client_id_env = _read_env_var_name(auth_cfg, "client_id_env")
    client_secret_env = _read_env_var_name(auth_cfg, "client_secret_env")

    client_id = os.environ.get(client_id_env)
    client_secret = os.environ.get(client_secret_env)
    if not client_id:
        raise ZerobusConfigError(f"Missing env var: {client_id_env}")
    if not client_secret:
        raise ZerobusConfigError(f"Missing env var: {client_secret_env}")

    sdk = ZerobusSdk(zerobus_endpoint, workspace_host)

    table_properties = TableProperties(table_name)
    stream_cfg = databricks_cfg.get("stream") if isinstance(databricks_cfg.get("stream"), dict) else {}
    options = StreamConfigurationOptions(
        record_type=RecordType.JSON,
        max_inflight_records=int(stream_cfg.get("max_inflight_records", 1000)),
        recovery=bool(stream_cfg.get("recovery", True)),
        flush_timeout_ms=int(stream_cfg.get("flush_timeout_ms", 60000)),
        server_lack_of_ack_timeout_ms=int(stream_cfg.get("server_lack_of_ack_timeout_ms", 60000)),
    )

    stream = await sdk.create_stream(client_id, client_secret, table_properties, options)
    err: Exception | None = None
    try:
        ack = await stream.ingest_record(record)
        await ack
        await stream.flush()
        return ZerobusTestResult(table_name=table_name, stream_id=stream.stream_id)
    except Exception as e:
        err = e
        raise
    finally:
        try:
            await stream.close()
        except Exception:
            # Don't mask the real ingest/create error with a close() error.
            if err is None:
                raise


def make_sample_bronze_record(source_name: str, endpoint: str) -> dict[str, Any]:
    """A record that matches the bronze table schema we created."""

    now = _utc_now_us()

    return {
        "event_time": now,
        "ingest_time": now,
        "source_name": source_name,
        "endpoint": endpoint,
        "namespace": 1,
        "node_id": "ns=1;s=Demo.Tag1",
        "browse_path": "Demo/Tag1",
        "status_code": 0,
        "status": "GOOD",
        "value_type": "Double",
        "value": "123.45",
        "value_num": 123.45,
        "raw": None,
    }
