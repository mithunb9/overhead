from __future__ import annotations

from typing import Any

import httpx

BASE_URL = "https://api.adsb.lol/v2"


async def fetch_nearby_aircraft(
    lat: float, lon: float, radius_nm: float, client: httpx.AsyncClient
) -> list[dict[str, Any]]:
    response = await client.get(f"{BASE_URL}/point/{lat}/{lon}/{radius_nm}")
    response.raise_for_status()
    return response.json().get("ac", [])
