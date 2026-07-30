from __future__ import annotations

import os
from typing import Any

import httpx

from overhead.cache import cached_call
from overhead.config import settings

BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
AEROAPI_KEY_ENV = "AEROAPI_API_KEY"


class _AuthError(Exception):
    """Raised on 401/403 so the None short-circuits out of cached_call without being cached."""


def _select_en_route(flights: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not flights:
        return None

    # /flights/{ident} spans ~14 days past through ~2 days of scheduled future legs,
    # so flights[0] can be a not-yet-departed leg with a different origin/destination
    # than the aircraft currently overhead. Prefer the departed-but-not-landed leg.
    for flight in flights:
        if flight.get("actual_off") and not flight.get("actual_on"):
            return flight

    return flights[0]


def _normalize(flight: dict[str, Any]) -> dict[str, Any]:
    origin = flight.get("origin") or {}
    destination = flight.get("destination") or {}

    return {
        "airline": None,
        "origin": {
            "iata_code": origin.get("code_iata"),
            "municipality": origin.get("city"),
        },
        "destination": {
            "iata_code": destination.get("code_iata"),
            "municipality": destination.get("city"),
        },
    }


async def fetch_aeroapi_route(callsign: str, client: httpx.AsyncClient) -> dict[str, Any] | None:
    # Key check and auth failures short-circuit outside cached_call: it caches "no
    # result" for origin_dest_ttl_s (24h), so caching a missing-key/bad-key None would
    # blind a self-hoster who fixes the key mid-window until the TTL expires.
    key = os.environ.get(AEROAPI_KEY_ENV)
    if not key:
        return None

    async def fetch() -> dict[str, Any] | None:
        response = await client.get(
            f"{BASE_URL}/flights/{callsign}", headers={"x-apikey": key}
        )

        if response.status_code in (401, 403):
            raise _AuthError

        if response.is_error:
            return None

        flights = response.json().get("flights", [])
        selected = _select_en_route(flights)
        return _normalize(selected) if selected else None

    try:
        return await cached_call(
            f"route:aeroapi:{callsign}", settings.cache.origin_dest_ttl_s, fetch
        )
    except _AuthError:
        return None
