import json
from unittest.mock import AsyncMock

import httpx
import pytest
import redis

from overhead.clients.adsbdb import fetch_flight_route
from overhead.config import settings


@pytest.mark.anyio
async def test_fetch_flight_route_returns_flightroute_on_success() -> None:
    payload = {"response": {"flightroute": {"callsign": "AAL2847"}}}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_flight_route("AAL2847", client)

    assert route == {"callsign": "AAL2847"}


@pytest.mark.anyio
async def test_fetch_flight_route_returns_none_on_404() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"response": "unknown callsign"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_flight_route("ZZZ9999", client)

    assert route is None


@pytest.mark.anyio
async def test_fetch_flight_route_returns_none_on_server_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_flight_route("AAL2847", client)

    assert route is None


@pytest.mark.anyio
async def test_fetch_flight_route_cache_hit_skips_http_call(stub_redis: AsyncMock) -> None:
    cached = {"callsign": "AAL2847"}
    stub_redis.get.return_value = json.dumps(cached).encode()

    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not hit adsbdb on a cache hit")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_flight_route("AAL2847", client)

    assert route == cached
    stub_redis.get.assert_awaited_once_with("route:adsbdb:AAL2847")


@pytest.mark.anyio
async def test_fetch_flight_route_cache_miss_calls_api_and_populates_cache(
    stub_redis: AsyncMock,
) -> None:
    payload = {"response": {"flightroute": {"callsign": "AAL2847"}}}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_flight_route("AAL2847", client)

    assert route == {"callsign": "AAL2847"}
    stub_redis.set.assert_awaited_once_with(
        "route:adsbdb:AAL2847", json.dumps(route), ex=settings.cache.origin_dest_ttl_s
    )


@pytest.mark.anyio
async def test_fetch_flight_route_caches_unknown_callsign_result(stub_redis: AsyncMock) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"response": "unknown callsign"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_flight_route("ZZZ9999", client)

    assert route is None
    stub_redis.set.assert_awaited_once_with(
        "route:adsbdb:ZZZ9999", json.dumps(None), ex=settings.cache.origin_dest_ttl_s
    )


@pytest.mark.anyio
async def test_fetch_flight_route_falls_through_on_redis_failure(stub_redis: AsyncMock) -> None:
    stub_redis.get.side_effect = redis.RedisError("connection refused")
    stub_redis.set.side_effect = redis.RedisError("connection refused")
    payload = {"response": {"flightroute": {"callsign": "AAL2847"}}}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        route = await fetch_flight_route("AAL2847", client)

    assert route == {"callsign": "AAL2847"}
