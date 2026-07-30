import json
import os
from unittest.mock import AsyncMock

import httpx
import pytest

from overhead.clients.aeroapi import AEROAPI_KEY_ENV, fetch_aeroapi_route
from overhead.config import settings

FUTURE_LEG = {
    "actual_off": None,
    "actual_on": None,
    "origin": {"code_iata": "ORD", "city": "Chicago"},
    "destination": {"code_iata": "LAX", "city": "Los Angeles"},
}
EN_ROUTE_LEG = {
    "actual_off": "2026-07-29T14:00:00Z",
    "actual_on": None,
    "origin": {"code_iata": "DFW", "city": "Dallas-Fort Worth"},
    "destination": {"code_iata": "ORD", "city": "Chicago"},
}


@pytest.mark.anyio
async def test_missing_key_returns_none_without_http_or_cache(
    monkeypatch: pytest.MonkeyPatch, stub_redis: AsyncMock
) -> None:
    monkeypatch.delenv(AEROAPI_KEY_ENV, raising=False)

    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call AeroAPI without a key")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_aeroapi_route("AAL2847", client)

    assert route is None
    stub_redis.set.assert_not_awaited()


@pytest.mark.anyio
async def test_selects_en_route_leg_and_normalizes(
    monkeypatch: pytest.MonkeyPatch, stub_redis: AsyncMock
) -> None:
    monkeypatch.setenv(AEROAPI_KEY_ENV, "secret")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-apikey"] == "secret"
        return httpx.Response(200, json={"flights": [FUTURE_LEG, EN_ROUTE_LEG]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_aeroapi_route("AAL2847", client)

    assert route == {
        "airline": None,
        "origin": {"iata_code": "DFW", "municipality": "Dallas-Fort Worth"},
        "destination": {"iata_code": "ORD", "municipality": "Chicago"},
    }
    stub_redis.set.assert_awaited_once_with(
        "route:aeroapi:AAL2847", json.dumps(route), ex=settings.cache.origin_dest_ttl_s
    )


@pytest.mark.anyio
async def test_empty_flights_returns_none(
    monkeypatch: pytest.MonkeyPatch, stub_redis: AsyncMock
) -> None:
    monkeypatch.setenv(AEROAPI_KEY_ENV, "secret")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"flights": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_aeroapi_route("ZZZ9999", client)

    assert route is None


@pytest.mark.anyio
@pytest.mark.parametrize("status", [401, 403])
async def test_auth_failure_returns_none_without_caching(
    status: int, monkeypatch: pytest.MonkeyPatch, stub_redis: AsyncMock
) -> None:
    monkeypatch.setenv(AEROAPI_KEY_ENV, "bad-key")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_aeroapi_route("AAL2847", client)

    assert route is None
    stub_redis.set.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.skipif(
    not os.environ.get(AEROAPI_KEY_ENV),
    reason=f"requires a real {AEROAPI_KEY_ENV} to hit the live AeroAPI service",
)
async def test_live_aeroapi_response_matches_normalized_shape() -> None:
    """Mocked tests above only prove our own parsing logic is internally consistent;
    this hits the real API to catch drift if AeroAPI ever changes its response shape."""
    async with httpx.AsyncClient() as client:
        route = await fetch_aeroapi_route("AAL100", client)

    if route is None:
        pytest.skip("no route resolved for AAL100 (no data in window, or key invalid/revoked)")

    assert set(route) == {"airline", "origin", "destination"}
    assert route["airline"] is None
    for leg in (route["origin"], route["destination"]):
        assert set(leg) == {"iata_code", "municipality"}
        assert leg["iata_code"] is None or isinstance(leg["iata_code"], str)
        assert leg["municipality"] is None or isinstance(leg["municipality"], str)
