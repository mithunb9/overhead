from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from overhead.config import settings
from overhead.main import app
from overhead.models.overhead import OverheadResponse

client = TestClient(app)

GROUND_AC = {
    "hex": "aa2ba1",
    "flight": "UAL2681 ",
    "r": "N75425",
    "t": "B739",
    "alt_baro": "ground",
    "gs": 0.0,
    "seen_pos": 1.9,
    "dst": 1.36,
}
GA_AC = {
    "hex": "ab4f82",
    "flight": "N828KP  ",
    "r": "N828KP",
    "t": "SR22",
    "alt_baro": 900,
    "gs": 94.0,
    "seen_pos": 0.05,
    "dst": 4.66,
}
STALE_AC = {
    "hex": "a80595",
    "flight": "FFT4593 ",
    "r": "N616FR",
    "t": "A21N",
    "alt_baro": 5000,
    "gs": 250.0,
    "seen_pos": 120,
    "dst": 3.0,
}
NEAREST_AC = {
    "hex": "abcd12",
    "flight": "AAL2847 ",
    "r": "N832AA",
    "t": "B738",
    "alt_baro": 32000,
    "gs": 447.0,
    "seen_pos": 3,
    "dst": 3.65,
}
FARTHER_AC = {
    "hex": "abcd34",
    "flight": "DAL100  ",
    "r": "N123DL",
    "t": "A320",
    "alt_baro": 28000,
    "gs": 400.0,
    "seen_pos": 2,
    "dst": 10.0,
}
ROUTE_RESPONSE = {
    "airline": {"name": "American Airlines", "icao": "AAL", "iata": "AA"},
    "origin": {"iata_code": "DFW", "municipality": "Dallas-Fort Worth"},
    "destination": {"iata_code": "ORD", "municipality": "Chicago"},
}


@pytest.fixture(autouse=True)
def mock_clients(monkeypatch: pytest.MonkeyPatch) -> tuple[AsyncMock, AsyncMock]:
    fetch_nearby = AsyncMock(return_value=[])
    fetch_route = AsyncMock(return_value=None)
    monkeypatch.setattr("overhead.api.routes.overhead.fetch_nearby_aircraft", fetch_nearby)
    monkeypatch.setattr("overhead.api.routes.overhead.fetch_flight_route", fetch_route)
    return fetch_nearby, fetch_route


def test_overhead_returns_nearest_commercial_flight(mock_clients: tuple[AsyncMock, AsyncMock]) -> None:
    fetch_nearby, fetch_route = mock_clients
    fetch_nearby.return_value = [GROUND_AC, GA_AC, STALE_AC, NEAREST_AC, FARTHER_AC]
    fetch_route.return_value = ROUTE_RESPONSE

    response = client.post("/overhead", json={"lat": 33.94, "lon": -118.41})

    assert response.status_code == 200
    body = response.json()
    assert body == [
        {
            "flight": "AA2847",
            "callsign": "AAL2847",
            "airline": "American Airlines",
            "airline_icao": "AAL",
            "reg": "N832AA",
            "actype": "B738",
            "origin": "DFW",
            "origin_city": "Dallas-Fort Worth",
            "dest": "ORD",
            "dest_city": "Chicago",
            "alt_ft": 32000,
            "speed_kt": 447.0,
            "dist_mi": pytest.approx(3.65 * 1.15078),
            "source": "adsb.lol",
            "age_s": 3,
        }
    ]
    fetch_route.assert_awaited_once()
    assert fetch_route.await_args.args[0] == "AAL2847"


def test_overhead_returns_requested_count_sorted_nearest_first(
    mock_clients: tuple[AsyncMock, AsyncMock],
) -> None:
    fetch_nearby, fetch_route = mock_clients
    fetch_nearby.return_value = [FARTHER_AC, NEAREST_AC]
    fetch_route.return_value = None

    response = client.post("/overhead", json={"lat": 33.94, "lon": -118.41, "count": 2})

    body = response.json()
    assert [flight["callsign"] for flight in body] == ["AAL2847", "DAL100"]
    assert body[0]["dist_mi"] < body[1]["dist_mi"]


def test_overhead_clamps_count_to_configured_max(mock_clients: tuple[AsyncMock, AsyncMock]) -> None:
    fetch_nearby, fetch_route = mock_clients
    fetch_nearby.return_value = [NEAREST_AC, FARTHER_AC]
    fetch_route.return_value = None

    with patch.object(settings.overhead, "count_max", 1):
        response = client.post("/overhead", json={"lat": 33.94, "lon": -118.41, "count": 5})

    assert len(response.json()) == 1


def test_overhead_returns_partial_list_when_fewer_aircraft_than_count(
    mock_clients: tuple[AsyncMock, AsyncMock],
) -> None:
    fetch_nearby, fetch_route = mock_clients
    fetch_nearby.return_value = [NEAREST_AC]
    fetch_route.return_value = None

    response = client.post("/overhead", json={"lat": 33.94, "lon": -118.41, "count": 5})

    assert len(response.json()) == 1


def test_overhead_falls_back_to_static_airline_table_when_route_unknown(
    mock_clients: tuple[AsyncMock, AsyncMock],
) -> None:
    fetch_nearby, fetch_route = mock_clients
    fetch_nearby.return_value = [NEAREST_AC]
    fetch_route.return_value = None

    response = client.post("/overhead", json={"lat": 33.94, "lon": -118.41})

    body = response.json()[0]
    assert body["airline"] == "American Airlines"
    assert body["airline_icao"] == "AAL"
    assert body["flight"] == "AA2847"
    assert body["origin"] is None
    assert body["dest"] is None


def test_overhead_returns_200_and_empty_list_when_nothing_overhead(
    mock_clients: tuple[AsyncMock, AsyncMock],
) -> None:
    fetch_nearby, _ = mock_clients
    fetch_nearby.return_value = [GROUND_AC, GA_AC, STALE_AC]

    response = client.post("/overhead", json={"lat": 33.94, "lon": -118.41})

    assert response.status_code == 200
    assert response.json() == []


def test_overhead_response_matches_model(mock_clients: tuple[AsyncMock, AsyncMock]) -> None:
    fetch_nearby, fetch_route = mock_clients
    fetch_nearby.return_value = [NEAREST_AC]
    fetch_route.return_value = ROUTE_RESPONSE

    response = client.post("/overhead", json={"lat": 33.94, "lon": -118.41})

    assert all(OverheadResponse.model_validate(flight) for flight in response.json())


def test_overhead_requires_lat_lon() -> None:
    response = client.post("/overhead", json={})

    assert response.status_code == 422


def test_overhead_rejects_get() -> None:
    response = client.get("/overhead")

    assert response.status_code == 405


def test_openapi_registers_overhead_route() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/overhead" in response.json()["paths"]
