from __future__ import annotations

import argparse
import asyncio
import os

from opcua2uc.config import load_config
from opcua2uc.core.bridge import Bridge
from opcua2uc.metrics import start_metrics_server
from opcua2uc.web.server import WebServer


async def amain() -> None:
    parser = argparse.ArgumentParser(description="OPC UA -> Zerobus Connector (edge)")
    parser.add_argument(
        "--config",
        default=os.environ.get("OPCUA2UC_CONFIG", "./config.yaml"),
        help="Path to YAML config (default: ./config.yaml or $OPCUA2UC_CONFIG)",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    bridge = Bridge(cfg)

    start_metrics_server(cfg.metrics_port)

    web_server = WebServer(bridge=bridge, config_path=args.config, port=cfg.web_port)

    await asyncio.gather(
        bridge.run_forever(),
        web_server.start(),
    )


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
