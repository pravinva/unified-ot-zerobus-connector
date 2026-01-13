from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from asyncua import Client


@dataclass
class OpcUaTestResult:
    ok: bool
    endpoint: str
    duration_ms: int | None = None
    server_application_name: str | None = None
    server_uri: str | None = None
    server_product_uri: str | None = None
    namespaces: int | None = None
    warning: str | None = None
    error: str | None = None


async def test_connection(endpoint: str, timeout_s: float = 5.0) -> OpcUaTestResult:
    """Connect/disconnect test.

    Prosys (and many servers) do NOT support reading Value on the Server object itself,
    so we avoid that and only read supported nodes/attributes.

    Success criteria: we can connect and disconnect.
    """

    start = time.time()
    client = Client(url=endpoint, timeout=timeout_s)

    try:
        await asyncio.wait_for(client.connect(), timeout=timeout_s)

        warn = None
        app_name = None
        app_uri = None
        product_uri = None
        namespaces = None

        # Best-effort: namespace array is a standard variable and usually readable.
        try:
            ns_arr = await client.nodes.server_namespace_array.read_value()
            namespaces = len(ns_arr) if isinstance(ns_arr, list) else None
        except Exception as e:
            warn = f"NamespaceArray read failed: {type(e).__name__}: {e}"

        # Best-effort: application description attributes (read attributes, not value)
        try:
            # These attribute reads are broadly supported.
            app_desc = await client.nodes.server.read_description()
            # app_desc is LocalizedText
            if app_desc is not None:
                app_name = str(getattr(app_desc, 'Text', app_desc))
        except Exception:
            pass

        # Some servers expose server status build info; try to read but don't require.
        try:
            status = await client.nodes.server_status.read_value()
            # status is ServerStatusDataType; fields vary.
            app_uri = getattr(getattr(status, 'BuildInfo', None), 'ProductUri', None) or app_uri
            product_uri = getattr(getattr(status, 'BuildInfo', None), 'ManufacturerName', None) or product_uri
        except Exception:
            pass

        return OpcUaTestResult(
            ok=True,
            endpoint=endpoint,
            duration_ms=int((time.time() - start) * 1000),
            server_application_name=app_name,
            server_uri=str(app_uri) if app_uri else None,
            server_product_uri=str(product_uri) if product_uri else None,
            namespaces=namespaces,
            warning=warn,
        )

    except Exception as e:
        return OpcUaTestResult(
            ok=False,
            endpoint=endpoint,
            duration_ms=int((time.time() - start) * 1000),
            error=f"{type(e).__name__}: {e}",
        )

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
