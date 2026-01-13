from __future__ import annotations

import asyncio
import time
from typing import Any, List, Tuple

from zerobus.sdk.shared import HeadersProvider

from opcua2uc.databricks_token import fetch_access_token


class CachingOAuthHeadersProvider(HeadersProvider):
    def __init__(self, databricks_cfg: dict[str, Any], table_name: str) -> None:
        self._cfg = databricks_cfg
        self._table_name = table_name
        self._token: str | None = None
        self._expires_at: int | None = None
        self._lock = asyncio.Lock()

    def _is_fresh(self) -> bool:
        if not self._token:
            return False
        if not self._expires_at:
            return True
        # Refresh a bit early
        return int(time.time()) < (self._expires_at - 60)

    def get_headers(self) -> List[Tuple[str, str]]:
        # SDK calls this synchronously; we bridge to async token fetch.
        # This is fine for our low-volume test endpoint; production would prefetch/refresh in background.
        if self._is_fresh():
            return [
                ("authorization", f"Bearer {self._token}"),
                ("x-databricks-zerobus-table-name", self._table_name),
            ]

        # Run token fetch in the current loop if possible, else create one.
        try:
            loop = asyncio.get_running_loop()
            # We're inside an event loop; block via a nested future.
            return loop.run_until_complete(self._refresh_and_headers())  # type: ignore[attr-defined]
        except RuntimeError:
            return asyncio.run(self._refresh_and_headers())

    async def _refresh_and_headers(self) -> List[Tuple[str, str]]:
        async with self._lock:
            if self._is_fresh():
                return [
                    ("authorization", f"Bearer {self._token}"),
                    ("x-databricks-zerobus-table-name", self._table_name),
                ]

            token, exp, _ = await fetch_access_token(self._cfg)
            self._token = token
            self._expires_at = exp

            return [
                ("authorization", f"Bearer {self._token}"),
                ("x-databricks-zerobus-table-name", self._table_name),
            ]
