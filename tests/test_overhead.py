from fastapi.testclient import TestClient

from flights_api.main import app
from flights_api.models.overhead import OverheadResponse

client = TestClient(app)


def test_overhead_returns_200() -> None:
    response = client.post("/overhead")

    assert response.status_code == 200


def test_overhead_returns_hello_world() -> None:
    response = client.post("/overhead")

    assert response.json() == {"message": "Hello World"}


def test_overhead_response_matches_model() -> None:
    response = client.post("/overhead")

    assert OverheadResponse.model_validate(response.json())


def test_overhead_rejects_get() -> None:
    response = client.get("/overhead")

    assert response.status_code == 405


def test_openapi_registers_overhead_route() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/overhead" in response.json()["paths"]
