from datetime import date

import pandas as pd
import pytest

from winddesk.service import OutOfWindowError, WindDeskService

T = pd.Timestamp


@pytest.mark.parametrize(
    ("auction_id", "offset"), [("epex_60", 1007), ("n2ex_60", 1009), ("epex_30", 1015)]
)
def test_each_auction_uses_the_last_run_before_its_gate_closure(
    service: WindDeskService, auction_id: str, offset: int
) -> None:
    hours = service.datasets[auction_id].hours  # type: ignore[index]
    assert len(hours) == 72
    assert (hours["error_mw"] == offset).all()


def test_meta(service: WindDeskService) -> None:
    meta = service.meta()
    assert meta.delivery_days == [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4)]
    assert meta.window_start == T("2026-01-01T23:00Z")
    assert meta.data.actual_half_hours_expected == 144
    assert meta.data.actual_half_hours_present == 144
    assert meta.data.forecast_runs == 25
    assert meta.data.forecast_rows_valid < meta.data.forecast_rows


def test_delivery_day(service: WindDeskService) -> None:
    view = service.delivery_day(date(2026, 1, 3), "epex_60")
    assert (view.window_start, view.window_end) == (T("2026-01-02T23:00Z"), T("2026-01-03T23:00Z"))
    assert view.decision.cutoff == T("2026-01-02T09:20Z")
    assert view.decision.runs_used == [T("2026-01-02T07:30Z")]
    assert view.decision.lead_hours_min == pytest.approx(15.5)
    assert view.decision.lead_hours_max == pytest.approx(38.5)
    assert len(view.hours) == 24
    assert len(view.actuals_half_hourly) == 48
    assert [run.publish_time for run in view.later_runs] == [
        T("2026-01-02T09:30Z"),
        T("2026-01-02T15:30Z"),
        T("2026-01-02T22:30Z"),
    ]
    assert view.summary is not None
    assert view.summary.hours_compared == 24
    assert view.summary.error_gwh == pytest.approx(24 * 1.007, abs=0.01)
    assert view.summary.largest_miss_mw == pytest.approx(1007)


def test_delivery_day_outside_window_raises(service: WindDeskService) -> None:
    with pytest.raises(OutOfWindowError):
        service.delivery_day(date(2026, 1, 5), "epex_60")


def test_accuracy(service: WindDeskService) -> None:
    acc = service.accuracy("epex_60")
    assert acc.raw.n == 72
    assert acc.raw.bias_mw == pytest.approx(1007)
    assert acc.calibrated.mae_mw < acc.raw.mae_mw
    assert 0 <= acc.band_coverage <= 1
    assert acc.calibration.slope == pytest.approx(1.0, abs=1e-6)
    assert (acc.decision_lead_hours_min, acc.decision_lead_hours_max) == (15.5, 38.5)
    assert [g.key for g in acc.by_hour] == [str(h) for h in range(24)]
    assert [g.key for g in acc.daily] == ["2026-01-02", "2026-01-03", "2026-01-04"]
    assert acc.by_lead_time[0].key == "0"
    assert acc.by_lead_time[-1].key == "47"
    assert len(acc.series) == 72


def test_lead_time_never_uses_runs_published_too_late(service: WindDeskService) -> None:
    view = service.lead_time(date(2026, 1, 2), date(2026, 1, 3), hours_ahead=4)
    assert len(view.points) == 48
    with_forecast = [p for p in view.points if p.publish_time is not None]
    assert with_forecast
    assert all(p.start_time - p.publish_time >= pd.Timedelta(hours=4) for p in with_forecast)
    assert view.summary is not None


def test_lead_time_rejects_reversed_range(service: WindDeskService) -> None:
    with pytest.raises(OutOfWindowError):
        service.lead_time(date(2026, 1, 3), date(2026, 1, 2), hours_ahead=4)
