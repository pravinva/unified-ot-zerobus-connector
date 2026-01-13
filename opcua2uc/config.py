from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    web_port: int = 8080
    metrics_port: int = 9090

    # OPC UA sources to subscribe to (placeholder structure for now)
    sources: list[dict[str, Any]] = field(default_factory=list)

    # Databricks/Zerobus destination config (placeholder structure for now)
    databricks: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "AppConfig":
        return AppConfig(
            web_port=int(d.get("web_port", 8080)),
            metrics_port=int(d.get("metrics_port", 9090)),
            sources=list(d.get("sources", []) or []),
            databricks=dict(d.get("databricks", {}) or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "web_port": self.web_port,
            "metrics_port": self.metrics_port,
            "sources": self.sources,
            "databricks": self.databricks,
        }


def load_config(path: str | Path) -> AppConfig:
    p = Path(path)
    if not p.exists():
        return AppConfig()

    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping/object at the top level.")

    return AppConfig.from_dict(data)


def save_config(path: str | Path, cfg: AppConfig) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg.to_dict(), f, sort_keys=False)
