from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_PATH_ENV = "FLIGHTS_API_CONFIG"
DEFAULT_CONFIG_PATH = "config.yaml"


class OverheadConfig(BaseModel):
    radius_nm: float = 5
    count_max: int = 10


class CacheConfig(BaseModel):
    origin_dest_ttl_s: int = 86400
    position_ttl_s: int = 60


class Config(BaseModel):
    overhead: OverheadConfig = OverheadConfig()
    cache: CacheConfig = CacheConfig()


def load_config(path: str | Path | None = None) -> Config:
    resolved = Path(path or os.environ.get(CONFIG_PATH_ENV, DEFAULT_CONFIG_PATH))
    if not resolved.exists():
        return Config()

    with resolved.open() as f:
        raw = yaml.safe_load(f) or {}

    return Config.model_validate(raw)


settings = load_config()
