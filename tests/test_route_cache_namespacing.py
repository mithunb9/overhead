import json
from unittest.mock import AsyncMock

import httpx
import pytest

from overhead.clients.aeroapi import AEROAPI_KEY_ENV, fetch_aeroapi_route

ADSBDB_CACHED_ROUTE = {"callsign": "AAL2847", "airline": {"name": "stale adsbdb entry"}}


@pytest.mark.anyio
async def test_switching_route_source_does_not_serve_other_providers_cache_entry(
    monkeypatch: pytest.MonkeyPatch, stub_redis: AsyncMock
) -> None:
    """A cache entry written under route:adsbdb:{callsign} must never satisfy a
    route:aeroapi:{callsign} lookup for the same callsign, or switching route_source
    would silently serve the previous provider's (differently shaped) cached route."""
    monkeypatch.setenv(AEROAPI_KEY_ENV, "secret")

    async def stub_get(key: str) -> bytes | None:
        if key == "route:adsbdb:AAL2847":
            return json.dumps(ADSBDB_CACHED_ROUTE).encode()
        return None

    stub_redis.get.side_effect = stub_get

    aeroapi_called = False

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal aeroapi_called
        aeroapi_called = True
        return httpx.Response(
            200,
            json={
                "flights": [
                    {
                        "actual_off": "2026-07-29T14:00:00Z",
                        "actual_on": None,
                        "origin": {"code_iata": "DFW", "city": "Dallas-Fort Worth"},
                        "destination": {"code_iata": "ORD", "city": "Chicago"},
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_aeroapi_route("AAL2847", client)

    assert aeroapi_called, "aeroapi client hit adsbdb's cache entry instead of its own key"
    assert route != ADSBDB_CACHED_ROUTE
    stub_redis.get.assert_awaited_with("route:aeroapi:AAL2847")
