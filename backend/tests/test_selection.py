import numpy as np
import pandas as pd
import pytest

from winddesk.domain.selection import fixed_lead, latest_available, runs_between, valid_points

T = pd.Timestamp


def forecasts(*rows: tuple[str, str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "publish_time": pd.to_datetime([r[0] for r in rows], utc=True),
            "start_time": pd.to_datetime([r[1] for r in rows], utc=True),
            "generation_mw": [r[2] for r in rows],
        }
    )


def cutoffs(pairs: dict[str, str]) -> pd.Series:
    return pd.Series(
        pd.to_datetime(list(pairs.values()), utc=True),
        index=pd.DatetimeIndex(pd.to_datetime(list(pairs), utc=True), name="start_time"),
    )


def test_valid_points_drops_targets_before_publish() -> None:
    f = forecasts(
        ("2026-01-11T07:30Z", "2026-01-11T07:00Z", 1.0),
        ("2026-01-11T07:30Z", "2026-01-11T08:00Z", 2.0),
    )
    assert valid_points(f)["generation_mw"].tolist() == [2.0]


def test_picks_latest_run_at_or_before_cutoff_and_never_a_later_one() -> None:
    f = forecasts(
        ("2026-01-11T04:30Z", "2026-01-12T00:00Z", 100.0),
        ("2026-01-11T07:30Z", "2026-01-12T00:00Z", 200.0),
        ("2026-01-11T09:30Z", "2026-01-12T00:00Z", 300.0),
    )
    chosen = latest_available(f, cutoffs({"2026-01-12T00:00Z": "2026-01-11T09:20Z"}))
    row = chosen.loc[T("2026-01-12T00:00Z")]
    assert row["forecast_mw"] == 200.0
    assert row["publish_time"] == T("2026-01-11T07:30Z")
    assert row["lead_hours"] == pytest.approx(16.5)


def test_run_published_exactly_at_cutoff_is_available() -> None:
    f = forecasts(("2026-01-11T09:20Z", "2026-01-12T00:00Z", 100.0))
    chosen = latest_available(f, cutoffs({"2026-01-12T00:00Z": "2026-01-11T09:20Z"}))
    assert chosen["forecast_mw"].tolist() == [100.0]


def test_target_without_eligible_run_is_absent() -> None:
    f = forecasts(("2026-01-11T09:30Z", "2026-01-12T00:00Z", 300.0))
    assert latest_available(f, cutoffs({"2026-01-12T00:00Z": "2026-01-11T09:20Z"})).empty


def test_falls_back_to_older_run_when_latest_lacks_the_hour() -> None:
    f = forecasts(
        ("2026-01-11T04:30Z", "2026-01-12T05:00Z", 100.0),
        ("2026-01-11T07:30Z", "2026-01-12T04:00Z", 200.0),
    )
    chosen = latest_available(
        f,
        cutoffs(
            {"2026-01-12T04:00Z": "2026-01-11T09:20Z", "2026-01-12T05:00Z": "2026-01-11T09:20Z"}
        ),
    )
    assert chosen["forecast_mw"].tolist() == [200.0, 100.0]


def test_never_looks_ahead_on_random_data() -> None:
    rng = np.random.default_rng(7)
    publishes = pd.date_range("2026-01-10T00:30Z", periods=40, freq="3h")
    rows = [
        # Like WINDFOR: runs publish at :30, targets start on the hour.
        (p, p.floor("h") + pd.Timedelta(hours=h), float(rng.integers(0, 20000)))
        for p in publishes
        for h in range(-2, 49)
    ]
    f = pd.DataFrame(rows, columns=["publish_time", "start_time", "generation_mw"])
    targets = pd.date_range("2026-01-12T00:00Z", periods=48, freq="h", name="start_time")
    cut = pd.Series(
        targets - pd.to_timedelta(rng.integers(0, 40, len(targets)), unit="h"), index=targets
    )
    chosen = latest_available(f, cut)
    assert not chosen.empty
    assert (chosen["publish_time"] <= cut.loc[chosen.index]).all()
    assert (chosen["lead_hours"] >= 0).all()
    for target, row in chosen.iterrows():
        eligible = f[
            (f["start_time"] == target)
            & (f["publish_time"] <= cut[target])
            & (f["start_time"] >= f["publish_time"])
        ]
        assert row["publish_time"] == eligible["publish_time"].max()


def test_fixed_lead_respects_lead_and_cap() -> None:
    f = forecasts(
        ("2026-01-11T18:30Z", "2026-01-12T00:00Z", 100.0),  # lead 5.5 h
        ("2026-01-11T22:30Z", "2026-01-12T00:00Z", 200.0),  # lead 1.5 h
    )
    targets = pd.DatetimeIndex([T("2026-01-12T00:00Z")], name="start_time")
    assert fixed_lead(f, targets, lead_hours=4, max_lead_hours=48)["forecast_mw"].tolist() == [
        100.0
    ]
    assert fixed_lead(f, targets, lead_hours=0, max_lead_hours=48)["forecast_mw"].tolist() == [
        200.0
    ]
    assert fixed_lead(f, targets, lead_hours=4, max_lead_hours=5).empty


def test_runs_between_returns_runs_after_cutoff_before_delivery() -> None:
    f = forecasts(
        ("2026-01-11T07:30Z", "2026-01-12T00:00Z", 1.0),  # before cutoff
        ("2026-01-11T15:30Z", "2026-01-12T00:00Z", 2.0),  # inside
        ("2026-01-11T15:30Z", "2026-01-13T00:00Z", 3.0),  # outside window
        ("2026-01-12T02:30Z", "2026-01-12T05:00Z", 4.0),  # published after delivery start
    )
    later = runs_between(
        f,
        after=T("2026-01-11T09:20Z"),
        before=T("2026-01-11T23:00Z"),
        window_start=T("2026-01-11T23:00Z"),
        window_end=T("2026-01-12T23:00Z"),
    )
    assert later["generation_mw"].tolist() == [2.0]
