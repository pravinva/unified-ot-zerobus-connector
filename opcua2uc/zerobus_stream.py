from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from zerobus.sdk.aio import ZerobusSdk, ZerobusStream
from zerobus.sdk.shared import RecordType, StreamConfigurationOptions, TableProperties


class ZerobusStreamError(RuntimeError):
    pass


@dataclass
class ZerobusTarget:
    workspace_host: str
    zerobus_endpoint: str
    table_name: str
    client_id: str
    client_secret: str
    stream_cfg: dict[str, Any]


class ZerobusStreamManager:
    def __init__(self, target: ZerobusTarget) -> None:
        self._target = target
        # The SDK/stream can enter a bad internal state after certain failures.
        # We keep the ability to recreate the SDK instance as part of recovery.
        self._sdk = ZerobusSdk(target.zerobus_endpoint, target.workspace_host.rstrip("/"))
        self._stream: ZerobusStream | None = None
        # _lock guards stream creation/swap/close; _io_lock serializes ingest/flush
        # across sources (the SDK stream is not safe to use concurrently).
        self._lock = asyncio.Lock()
        self._io_lock = asyncio.Lock()

    @staticmethod
    def _is_stream_closed_error(e: Exception) -> bool:
        msg = str(e).lower()
        # SDK error strings we've seen in the field:
        # - "Cannot ingest records after stream is closed or before it's opened"
        # - "Error happened in receiving records: invalid state"
        return (
            ("stream is closed" in msg)
            or ("before it's opened" in msg)
            or ("invalid state" in msg)
            or ("error happened in receiving records" in msg)
        )

    async def _reset_sdk_and_stream(self) -> None:
        """Best-effort: close current stream and recreate SDK so we can recover from poisoned states."""
        async with self._lock:
            if self._stream is not None:
                try:
                    await self._stream.close()
                except Exception:
                    pass
                finally:
                    self._stream = None
            # Create a fresh SDK instance (old one may be in a bad internal state).
            self._sdk = ZerobusSdk(self._target.zerobus_endpoint, self._target.workspace_host.rstrip("/"))

    async def get_or_create(self) -> ZerobusStream:
        async with self._lock:
            if self._stream is not None:
                return self._stream

            opts = StreamConfigurationOptions(
                record_type=RecordType.JSON,
                max_inflight_records=int(self._target.stream_cfg.get("max_inflight_records", 1000)),
                recovery=bool(self._target.stream_cfg.get("recovery", True)),
                flush_timeout_ms=int(self._target.stream_cfg.get("flush_timeout_ms", 60000)),
                server_lack_of_ack_timeout_ms=int(self._target.stream_cfg.get("server_lack_of_ack_timeout_ms", 60000)),
            )

            table_props = TableProperties(self._target.table_name)
            self._stream = await self._sdk.create_stream(self._target.client_id, self._target.client_secret, table_props, opts)
            return self._stream

    async def ingest_one(self, record: dict[str, Any]) -> None:
        # Serialize against flush/other ingests and self-heal if the SDK
        # says the stream was closed/not opened.
        async with self._io_lock:
            last_err: Exception | None = None
            for _ in range(2):
                stream = await self.get_or_create()
                try:
                    ack_future = await stream.ingest_record(record)
                    await ack_future
                    return
                except Exception as e:
                    last_err = e
                    if self._is_stream_closed_error(e):
                        # Stream/SDK is likely poisoned: reset and retry once.
                        await self._reset_sdk_and_stream()
                        continue
                    raise
            assert last_err is not None
            raise last_err

    async def flush(self) -> None:
        # Only flush if we've created a stream at least once.
        if self._stream is None:
            return
        async with self._io_lock:
            last_err: Exception | None = None
            for _ in range(2):
                if self._stream is None:
                    return
                try:
                    await self._stream.flush()
                    return
                except Exception as e:
                    last_err = e
                    if self._is_stream_closed_error(e):
                        await self._reset_sdk_and_stream()
                        continue
                    raise
            assert last_err is not None
            raise last_err

    async def close(self) -> None:
        async with self._lock:
            if self._stream is None:
                return
            try:
                await self._stream.close()
            finally:
                self._stream = None
