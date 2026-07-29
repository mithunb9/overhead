import json
from unittest.mock import AsyncMock

import httpx
import pytest
import redis

from flights_api.clients.adsb_lol import fetch_nearby_aircraft
from flights_api.config import settings


@pytest.mark.anyio
async def test_fetch_nearby_aircraft_returns_ac_list_on_success() -> None:
    payload = {"ac": [{"hex": "abcd12", "flight": "AAL2847 "}]}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        aircraft = await fetch_nearby_aircraft(33.94, -118.41, 5, client)

    assert aircraft == [{"hex": "abcd12", "flight": "AAL2847 "}]


@pytest.mark.anyio
async def test_fetch_nearby_aircraft_defaults_to_empty_list_when_ac_missing() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        aircraft = await fetch_nearby_aircraft(33.94, -118.41, 5, client)

    assert aircraft == []


@pytest.mark.anyio
async def test_fetch_nearby_aircraft_raises_on_server_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_nearby_aircraft(33.94, -118.41, 5, client)


@pytest.mark.anyio
async def test_fetch_nearby_aircraft_cache_hit_skips_http_call(stub_redis: AsyncMock) -> None:
    cached = [{"hex": "cached01", "flight": "CACHED1"}]
    stub_redis.get.return_value = json.dumps(cached).encode()

    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not hit adsb.lol on a cache hit")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        aircraft = await fetch_nearby_aircraft(33.94, -118.41, 5, client)

    assert aircraft == cached
    stub_redis.get.assert_awaited_once_with("adsb:33.94:-118.41:5")


@pytest.mark.anyio
async def test_fetch_nearby_aircraft_cache_miss_calls_api_and_populates_cache(
    stub_redis: AsyncMock,
) -> None:
    payload = {"ac": [{"hex": "abcd12", "flight": "AAL2847 "}]}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        aircraft = await fetch_nearby_aircraft(33.94, -118.41, 5, client)

    assert aircraft == payload["ac"]
    stub_redis.set.assert_awaited_once_with(
        "adsb:33.94:-118.41:5", json.dumps(payload["ac"]), ex=settings.cache.position_ttl_s
    )


@pytest.mark.anyio
async def test_fetch_nearby_aircraft_falls_through_on_redis_failure(stub_redis: AsyncMock) -> None:
    stub_redis.get.side_effect = redis.RedisError("connection refused")
    stub_redis.set.side_effect = redis.RedisError("connection refused")
    payload = {"ac": [{"hex": "abcd12", "flight": "AAL2847 "}]}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        aircraft = await fetch_nearby_aircraft(33.94, -118.41, 5, client)

    assert aircraft == payload["ac"]
