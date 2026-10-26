from pathlib import Path

import pandas as pd

from winddesk.repository import load_snapshot, write_snapshot


def _frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    actuals = pd.DataFrame(
        {
            "start_time": pd.to_datetime(["2026-01-01T23:00Z", "2026-01-01T23:30Z"], utc=True),
            "settlement_date": ["2026-01-01", "2026-01-01"],
            "settlement_period": [47, 48],
            "generation_mw": [9130.0, 8849.0],
        }
    )
    forecasts = pd.DataFrame(
        {
            "publish_time": pd.to_datetime(["2026-01-01T07:30Z"], utc=True),
            "start_time": pd.to_datetime(["2026-01-02T00:00Z"], utc=True),
            "generation_mw": [12000.0],
        }
    )
    return actuals, forecasts


def test_snapshot_roundtrip_preserves_values_and_utc(tmp_path: Path) -> None:
    actuals, forecasts = _frames()
    write_snapshot(tmp_path, actuals, forecasts, {"fetched_at": "2026-10-26T12:00:00Z"})
    snap = load_snapshot(tmp_path)
    assert snap.actuals["start_time"].tolist() == actuals["start_time"].tolist()
    assert snap.actuals["generation_mw"].tolist() == [9130.0, 8849.0]
    assert snap.actuals["settlement_period"].tolist() == [47, 48]
    assert snap.forecasts["publish_time"].tolist() == forecasts["publish_time"].tolist()
    assert str(snap.forecasts["start_time"].dt.tz) == "UTC"
    assert snap.manifest["fetched_at"] == "2026-10-26T12:00:00Z"
    assert snap.manifest["files"]["actuals.csv.gz"]["rows"] == 2
    assert len(snap.manifest["files"]["forecasts.csv.gz"]["sha256"]) == 64


def test_snapshot_files_are_deterministic(tmp_path: Path) -> None:
    actuals, forecasts = _frames()
    write_snapshot(tmp_path / "a", actuals, forecasts, {})
    write_snapshot(tmp_path / "b", actuals, forecasts, {})
    for name in ("actuals.csv.gz", "forecasts.csv.gz"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
