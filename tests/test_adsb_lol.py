import httpx
import pytest

from flights_api.clients.adsb_lol import fetch_nearby_aircraft


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
