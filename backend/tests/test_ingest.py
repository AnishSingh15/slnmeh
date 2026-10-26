from datetime import UTC, date, datetime

import httpx
import pandas as pd
import pytest
import respx

from winddesk.ingest.elexon import BASE_URL, ElexonClient, ElexonError

FUELHH_URL = f"{BASE_URL}/datasets/FUELHH/stream"
WINDFOR_URL = f"{BASE_URL}/datasets/WINDFOR/stream"
PUBLISH_FROM = datetime(2025, 12, 29, tzinfo=UTC)
PUBLISH_TO = datetime(2026, 2, 1, 23, tzinfo=UTC)


def _fuelhh(start: str, period: int, mw: int, fuel: str = "WIND") -> dict[str, object]:
    return {
        "dataset": "FUELHH",
        "publishTime": "2026-01-02T00:00:00Z",
        "startTime": start,
        "settlementDate": "2026-01-01",
        "settlementPeriod": period,
        "fuelType": fuel,
        "generation": mw,
    }


@respx.mock
def test_wind_actuals_requests_wind_and_normalises() -> None:
    route = respx.get(FUELHH_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                _fuelhh("2026-01-01T23:30:00Z", 48, 8849),
                _fuelhh("2026-01-01T23:00:00Z", 47, 9130),
                _fuelhh("2026-01-01T23:00:00Z", 47, 500, fuel="CCGT"),
            ],
        )
    )
    frame = ElexonClient().wind_actuals(date(2026, 1, 1), date(2026, 2, 1))
    params = route.calls.last.request.url.params
    assert params["fuelType"] == "WIND"
    assert params["settlementDateFrom"] == "2026-01-01"
    assert params["settlementDateTo"] == "2026-02-01"
    assert list(frame.columns) == [
        "start_time",
        "settlement_date",
        "settlement_period",
        "generation_mw",
    ]
    assert frame["start_time"].tolist() == [
        pd.Timestamp("2026-01-01T23:00Z"),
        pd.Timestamp("2026-01-01T23:30Z"),
    ]
    assert frame["generation_mw"].tolist() == [9130.0, 8849.0]


@respx.mock
def test_wind_forecasts_sends_publish_window_and_drops_duplicates() -> None:
    row = {"publishTime": "2026-01-01T07:30:00Z", "startTime": "2026-01-02T00:00:00Z"}
    route = respx.get(WINDFOR_URL).mock(
        return_value=httpx.Response(
            200, json=[{**row, "generation": 11000}, {**row, "generation": 12000}]
        )
    )
    frame = ElexonClient().wind_forecasts(PUBLISH_FROM, PUBLISH_TO)
    params = route.calls.last.request.url.params
    assert params["publishDateTimeFrom"] == "2025-12-29T00:00:00Z"
    assert params["publishDateTimeTo"] == "2026-02-01T23:00:00Z"
    assert list(frame.columns) == ["publish_time", "start_time", "generation_mw"]
    assert frame["generation_mw"].tolist() == [12000.0]


@respx.mock
def test_server_errors_are_retried() -> None:
    route = respx.get(WINDFOR_URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json=[])]
    )
    frame = ElexonClient(backoff_seconds=0).wind_forecasts(PUBLISH_FROM, PUBLISH_TO)
    assert route.call_count == 2
    assert frame.empty


@respx.mock
def test_client_errors_fail_fast() -> None:
    route = respx.get(WINDFOR_URL).mock(return_value=httpx.Response(400))
    with pytest.raises(ElexonError, match="HTTP 400"):
        ElexonClient(backoff_seconds=0).wind_forecasts(PUBLISH_FROM, PUBLISH_TO)
    assert route.call_count == 1


@respx.mock
def test_missing_fields_are_rejected() -> None:
    respx.get(WINDFOR_URL).mock(
        return_value=httpx.Response(200, json=[{"publishTime": "2026-01-01T07:30:00Z"}])
    )
    with pytest.raises(ElexonError, match="missing"):
        ElexonClient(backoff_seconds=0).wind_forecasts(PUBLISH_FROM, PUBLISH_TO)
