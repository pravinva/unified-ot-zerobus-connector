from __future__ import annotations

from typing import Any

from opcua2uc.databricks_token import DatabricksAuthError, fetch_access_token


async def oauth_client_credentials_token(databricks_cfg: dict[str, Any]) -> dict[str, Any]:
    """Return token metadata (never the raw token)."""

    token, exp, url = await fetch_access_token(databricks_cfg)
    return {
        "ok": True,
        "token_type": "Bearer",
        "scope": (databricks_cfg.get("auth") or {}).get("scope", "all-apis"),
        "expires_at_unix": exp,
        "token_preview": f"{token[:6]}…{token[-4:]}",
        "token_endpoint_used": url,
    }
