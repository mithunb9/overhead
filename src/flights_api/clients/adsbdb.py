from __future__ import annotations

from typing import Any

import httpx

from flights_api.cache import cached_call
from flights_api.config import settings

BASE_URL = "https://api.adsbdb.com/v0"


async def fetch_flight_route(callsign: str, client: httpx.AsyncClient) -> dict[str, Any] | None:
    async def fetch() -> dict[str, Any] | None:
        response = await client.get(f"{BASE_URL}/callsign/{callsign}")

        # adsbdb is community-sourced and returns 404 for "route unknown"; treat any
        # other failure the same way rather than let a secondary enrichment call
        # take down the whole /overhead response.
        if response.is_error:
            return None

        return response.json().get("response", {}).get("flightroute")

    return await cached_call(f"route:{callsign}", settings.cache.origin_dest_ttl_s, fetch)
