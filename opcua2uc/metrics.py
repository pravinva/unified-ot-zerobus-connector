from __future__ import annotations

from prometheus_client import Counter, Gauge, start_http_server


EVENTS_INGESTED = Counter("opcua2uc_events_ingested_total", "Events ingested from OPC UA")
EVENTS_SENT = Counter("opcua2uc_events_sent_total", "Events sent to Databricks via Zerobus")
CONNECTED_SOURCES = Gauge("opcua2uc_connected_sources", "Currently connected OPC UA sources")

EVENTS_DROPPED = Counter(
    "opcua2uc_events_dropped_total",
    "Events dropped due to backpressure",
    ["source"],
)
QUEUE_DEPTH = Gauge(
    "opcua2uc_queue_depth",
    "Current in-memory queue depth",
    ["source"],
)


def start_metrics_server(port: int) -> None:
    """Start the Prometheus metrics server.

    In dev it's easy to have multiple connector processes. If the configured
    port is already bound, don't crash the connector.
    """

    try:
        start_http_server(port)
    except OSError as e:
        if getattr(e, "errno", None) in (48, 98):
            return
        raise
