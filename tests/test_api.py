from fastapi.testclient import TestClient
from src.api.server import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_tile_endpoint_creates_tile():
    client = TestClient(app)
    r = client.get("/tiles/ndvi/0/0/0.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_report_parcel():
    client = TestClient(app)
    r = client.get("/report/parcel/1")
    assert r.status_code == 200
    j = r.json()
    assert "png" in j and "metrics" in j

