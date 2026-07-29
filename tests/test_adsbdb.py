import httpx
import pytest

from flights_api.clients.adsbdb import fetch_flight_route


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
