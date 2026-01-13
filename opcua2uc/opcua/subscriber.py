from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable

from asyncua import Client, ua
from asyncua.common.node import Node


@dataclass
class OpcUaRecord:
    source_name: str
    endpoint: str
    namespace: int
    node_id: str
    browse_path: str | None
    status_code: int | None
    status: str | None
    value_type: str
    value: str
    value_num: float | None
    event_time_ms: int


def _now_ms() -> int:
    return int(time.time() * 1000)


def _coerce_value(v: Any) -> tuple[str, str, float | None]:
    if v is None:
        return "Null", "", None
    if isinstance(v, bool):
        return "Boolean", "true" if v else "false", 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return type(v).__name__, str(v), float(v)
    return type(v).__name__, str(v), None


async def _node_browse_path(node: Node) -> str | None:
    try:
        path = await node.get_path(as_string=True)
        if isinstance(path, list):
            return "/".join(path)
        return str(path)
    except Exception:
        return None


async def _find_simulation_root(objects: Node) -> Node:
    """Prefer Prosys Simulation folder if present."""
    try:
        children = await objects.get_children()
    except Exception:
        return objects

    for c in children:
        try:
            bn = await c.read_browse_name()
            name = getattr(bn, "Name", None) or str(bn)
            if isinstance(name, str) and name.lower().startswith("simulation"):
                return c
        except Exception:
            continue

    return objects


async def _browse_variable_nodes(root: Node, limit: int = 25) -> list[Node]:
    out: list[Node] = []
    stack: list[Node] = [root]

    while stack and len(out) < limit:
        n = stack.pop()
        try:
            children = await n.get_children()
        except Exception:
            continue

        for c in children:
            if len(out) >= limit:
                break
            try:
                cls = await c.read_node_class()
                if cls == ua.NodeClass.Variable:
                    out.append(c)
                    continue
            except Exception:
                pass
            stack.append(c)

    return out


class _SubHandler:
    def __init__(self, make_record: Callable[[Node, Any, Any], OpcUaRecord], on_record: Callable[[OpcUaRecord], None]):
        self._make_record = make_record
        self._on_record = on_record

    def datachange_notification(self, node: Node, val, data):
        try:
            rec = self._make_record(node, val, data)
            self._on_record(rec)
        except Exception:
            pass


async def run_subscription(
    *,
    source_name: str,
    endpoint: str,
    on_record: Callable[[OpcUaRecord], None],
    stop_evt: asyncio.Event,
    on_stats: Callable[[dict[str, Any]], None] | None = None,
    variable_limit: int = 25,
    publishing_interval_ms: int = 1000,
) -> None:
    """Connect, auto-discover variables, subscribe until stop_evt is set."""

    client = Client(url=endpoint, timeout=5.0)
    await client.connect()

    try:
        objects = client.nodes.objects
        root = await _find_simulation_root(objects)
        nodes = await _browse_variable_nodes(root, limit=variable_limit)

        if on_stats is not None:
            on_stats({"discovered": len(nodes)})

        if not nodes:
            raise RuntimeError("No OPC UA variable nodes discovered under Objects/Simulation (or Objects)")

        browse_paths: dict[str, str | None] = {}
        for n in nodes:
            browse_paths[n.nodeid.to_string()] = await _node_browse_path(n)

        def make_record(node: Node, val: Any, data: Any) -> OpcUaRecord:
            vt, vs, vn = _coerce_value(val)
            nid = node.nodeid.to_string()
            ns = int(getattr(node.nodeid, "NamespaceIndex", 0))
            return OpcUaRecord(
                source_name=source_name,
                endpoint=endpoint,
                namespace=ns,
                node_id=nid,
                browse_path=browse_paths.get(nid),
                status_code=None,
                status=None,
                value_type=vt,
                value=vs,
                value_num=vn,
                event_time_ms=_now_ms(),
            )

        handler = _SubHandler(make_record, on_record)
        sub = await client.create_subscription(publishing_interval_ms, handler)

        handles: list[Any] = []
        try:
            for n in nodes:
                try:
                    h = await sub.subscribe_data_change(n)
                    handles.append(h)
                except Exception:
                    continue

            if on_stats is not None:
                on_stats({"subscribed": len(handles)})

            if not handles:
                raise RuntimeError("Discovered nodes but could not subscribe to any (0 subscriptions succeeded)")

            while not stop_evt.is_set():
                await asyncio.sleep(0.25)

        finally:
            try:
                for h in handles:
                    try:
                        await sub.unsubscribe(h)
                    except Exception:
                        pass
                await sub.delete()
            except Exception:
                pass

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
