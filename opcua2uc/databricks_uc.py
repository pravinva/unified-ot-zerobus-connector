from __future__ import annotations

from typing import Any
from urllib.parse import quote

from aiohttp import ClientSession

from opcua2uc.databricks_token import fetch_access_token


class DatabricksUcError(RuntimeError):
    pass


async def get_table_schema(databricks_cfg: dict[str, Any], full_name: str) -> dict[str, Any]:
    """Fetch UC table metadata for a fully qualified table name (catalog.schema.table)."""

    host = (databricks_cfg.get("workspace_host") or "").strip().rstrip("/")
    if not host:
        raise DatabricksUcError("Missing databricks.workspace_host")

    token, _, _ = await fetch_access_token(databricks_cfg)

    url = f"{host}/api/2.1/unity-catalog/tables/{quote(full_name, safe='')}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers, timeout=20) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise DatabricksUcError(f"{url} -> HTTP {resp.status}: {text[:1000]}")
            return await resp.json()
