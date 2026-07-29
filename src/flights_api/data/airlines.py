from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

_AIRLINES_PATH = Path(__file__).with_name("airlines.json")


class AirlineEntry(TypedDict):
    name: str
    iata: str


@lru_cache(maxsize=1)
def load_airlines() -> dict[str, AirlineEntry]:
    with _AIRLINES_PATH.open() as f:
        return json.load(f)
