from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from winddesk.config import Settings
from winddesk.main import create_app
from winddesk.service import WindDeskService


@pytest.fixture
def client(service: WindDeskService) -> TestClient:
    return TestClient(create_app(Settings(static_dir=None), service=service))


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "data_fetched_at": "2026-10-26T12:00:00Z"}


def test_meta(client: TestClient) -> None:
    body = client.get("/api/meta").json()
    assert [a["id"] for a in body["auctions"]] == ["epex_60", "n2ex_60", "epex_30"]
    assert body["default_auction"] == "epex_60"
    assert body["delivery_days"][0] == "2026-01-02"
    assert body["window_start"] == "2026-01-01T23:00:00Z"


def test_delivery_day(client: TestClient) -> None:
    response = client.get("/api/delivery-day", params={"date": "2026-01-03", "auction": "n2ex_60"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["hours"]) == 24
    assert body["decision"]["runs_used"] == ["2026-01-02T09:30:00Z"]


def test_delivery_day_defaults_to_epex_60(client: TestClient) -> None:
    body = client.get("/api/delivery-day", params={"date": "2026-01-03"}).json()
    assert body["auction"]["id"] == "epex_60"


@pytest.mark.parametrize(
    "params",
    [
        {"date": "2026-03-01"},
        {"date": "2026-01-03", "auction": "nope"},
        {"date": "not-a-date"},
    ],
)
def test_delivery_day_rejects_bad_params(client: TestClient, params: dict[str, str]) -> None:
    assert client.get("/api/delivery-day", params=params).status_code == 422


def test_accuracy(client: TestClient) -> None:
    body = client.get("/api/accuracy", params={"auction": "epex_30"}).json()
    assert body["auction"]["id"] == "epex_30"
    assert body["raw"]["n"] == 72


def test_lead_time_defaults_to_whole_window(client: TestClient) -> None:
    body = client.get("/api/lead-time").json()
    assert body["hours_ahead"] == 4
    assert (body["start"], body["end"]) == ("2026-01-02", "2026-01-04")
    assert len(body["points"]) == 72


def test_lead_time_rejects_hours_over_48(client: TestClient) -> None:
    assert client.get("/api/lead-time", params={"hours": 49}).status_code == 422


def test_responses_are_gzipped(client: TestClient) -> None:
    response = client.get("/api/accuracy", headers={"Accept-Encoding": "gzip"})
    assert response.headers["content-encoding"] == "gzip"


def test_serves_spa_with_history_fallback(tmp_path: Path, service: WindDeskService) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<div id=root></div>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    spa = TestClient(create_app(Settings(static_dir=tmp_path), service=service))
    assert spa.get("/").text == "<div id=root></div>"
    assert spa.get("/accuracy").text == "<div id=root></div>"
    assert spa.get("/assets/app.js").text == "console.log(1)"
    assert spa.get("/favicon.svg").text == "<svg/>"
    assert spa.get("/api/unknown").status_code == 404
    assert spa.get("/api/health").status_code == 200
