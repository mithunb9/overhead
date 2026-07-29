from fastapi.testclient import TestClient

from flights_api.main import app

client = TestClient(app)


def test_overhead_returns_200() -> None:
    response = client.post("/overhead")

    assert response.status_code == 200


def test_overhead_returns_hello_world() -> None:
    response = client.post("/overhead")

    assert response.json() == {"message": "Hello World"}
