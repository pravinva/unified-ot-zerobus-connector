from __future__ import annotations

import os
import time
from typing import Any

from aiohttp import BasicAuth, ClientSession


class DatabricksAuthError(RuntimeError):
    pass


def _read_secret(cfg: dict[str, Any], key: str, env_key: str) -> str | None:
    direct = cfg.get(key)
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    env_name = cfg.get(env_key)
    if isinstance(env_name, str) and env_name.strip():
        return os.environ.get(env_name.strip())

    return None


async def fetch_access_token(databricks_cfg: dict[str, Any]) -> tuple[str, int | None, str]:
    """Return (access_token, expires_at_unix, token_endpoint_used)."""

    host = (databricks_cfg.get("workspace_host") or "").strip().rstrip("/")
    if not host:
        raise DatabricksAuthError("Missing databricks.workspace_host")

    auth_cfg = databricks_cfg.get("auth")
    if not isinstance(auth_cfg, dict):
        auth_cfg = {}

    client_id = _read_secret(auth_cfg, "client_id", "client_id_env")
    client_secret = _read_secret(auth_cfg, "client_secret", "client_secret_env")

    if not client_id:
        raise DatabricksAuthError("Missing client_id (set databricks.auth.client_id or databricks.auth.client_id_env)")
    if not client_secret:
        raise DatabricksAuthError(
            "Missing client_secret (set databricks.auth.client_secret or databricks.auth.client_secret_env)"
        )

    scope = (auth_cfg.get("scope") or "all-apis").strip() or "all-apis"

    # For this workspace we know /oidc/v1/token exists.
    token_paths = [
        "/oidc/v1/token",
        "/oidc/oauth2/v1/token",
    ]

    last_err = None
    async with ClientSession() as session:
        for path in token_paths:
            url = f"{host}{path}"
            data = {
                "grant_type": "client_credentials",
                "scope": scope,
            }
            auth = BasicAuth(login=client_id, password=client_secret)
            try:
                async with session.post(url, data=data, auth=auth, timeout=20) as resp:
                    text = await resp.text()
                    if resp.status == 404:
                        last_err = f"{url} -> HTTP {resp.status}: {text[:500]}"
                        continue
                    if resp.status >= 400:
                        raise DatabricksAuthError(f"{url} -> HTTP {resp.status}: {text[:500]}")

                    payload = await resp.json()
                    access_token = payload.get("access_token")
                    expires_in = payload.get("expires_in")
                    if not access_token:
                        raise DatabricksAuthError(f"Token response missing access_token from {url}")

                    now = int(time.time())
                    exp = None
                    try:
                        exp = now + int(expires_in)
                    except Exception:
                        exp = None

                    return str(access_token), exp, url
            except DatabricksAuthError:
                raise
            except Exception as e:
                last_err = f"{url} -> {type(e).__name__}: {e}"

    raise DatabricksAuthError(last_err or "Failed to fetch token")


import json


def _workspace_id_from_zerobus_endpoint(endpoint: str) -> str:
    # Expected: "<workspace_id>.zerobus.<region>.cloud.databricks.com"
    return endpoint.split('.', 1)[0]


async def fetch_zerobus_token(databricks_cfg: dict[str, Any], table_name: str) -> tuple[str, int | None, str]:
    """Fetch a Zerobus Direct Write token (matches zerobus-sdk-py request shape).

    Returns (access_token, expires_at_unix, token_endpoint_used).
    """

    zerobus_endpoint = (databricks_cfg.get('zerobus_endpoint') or '').strip()
    if not zerobus_endpoint:
        raise DatabricksAuthError('Missing databricks.zerobus_endpoint')

    workspace_id = str(databricks_cfg.get('workspace_id') or _workspace_id_from_zerobus_endpoint(zerobus_endpoint)).strip()
    if not workspace_id:
        raise DatabricksAuthError('Missing workspace_id (could not derive from zerobus_endpoint)')

    # Build authorization_details exactly like zerobus-sdk-py.
    three = table_name.split('.')
    if len(three) != 3:
        raise DatabricksAuthError("table_name must be catalog.schema.table")

    catalog_name, schema_name, tbl = three
    authorization_details = [
        {
            "type": "unity_catalog_privileges",
            "privileges": ["USE CATALOG"],
            "object_type": "CATALOG",
            "object_full_path": catalog_name,
        },
        {
            "type": "unity_catalog_privileges",
            "privileges": ["USE SCHEMA"],
            "object_type": "SCHEMA",
            "object_full_path": f"{catalog_name}.{schema_name}",
        },
        {
            "type": "unity_catalog_privileges",
            "privileges": ["SELECT", "MODIFY"],
            "object_type": "TABLE",
            "object_full_path": f"{catalog_name}.{schema_name}.{tbl}",
        },
    ]

    # Use the same request shape as SDK
    host = (databricks_cfg.get("workspace_host") or "").strip().rstrip("/")
    if not host:
        raise DatabricksAuthError("Missing databricks.workspace_host")

    auth_cfg = databricks_cfg.get("auth")
    if not isinstance(auth_cfg, dict):
        auth_cfg = {}

    client_id = _read_secret(auth_cfg, "client_id", "client_id_env")
    client_secret = _read_secret(auth_cfg, "client_secret", "client_secret_env")
    if not client_id or not client_secret:
        raise DatabricksAuthError("Missing client_id/client_secret")

    url = f"{host}/oidc/v1/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "all-apis",
        "resource": f"api://databricks/workspaces/{workspace_id}/zerobusDirectWriteApi",
        "authorization_details": json.dumps(authorization_details),
    }

    auth = BasicAuth(login=client_id, password=client_secret)

    async with ClientSession() as session:
        async with session.post(url, data=data, auth=auth, timeout=20) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise DatabricksAuthError(f"{url} -> HTTP {resp.status}: {text[:500]}")

            payload = await resp.json()
            access_token = payload.get('access_token')
            expires_in = payload.get('expires_in')
            if not access_token:
                raise DatabricksAuthError('No access_token received')

            now = int(time.time())
            exp = None
            try:
                exp = now + int(expires_in)
            except Exception:
                exp = None

            return str(access_token), exp, url
