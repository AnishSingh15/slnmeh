from datetime import date

import numpy as np
import pandas as pd
import pytest

from winddesk.domain.calibration import Calibration, fit, leave_one_day_out

DAY_3 = date(2026, 1, 3)


def _hours() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    rows = []
    for day in (date(2026, 1, 2), DAY_3, date(2026, 1, 4)):
        for hour in range(6):
            forecast = 2000.0 + 1500 * hour + rng.normal(0, 100)
            actual = 300 + 0.8 * forecast + rng.normal(0, 200)
            rows.append({"delivery_day": day, "forecast_mw": forecast, "actual_mw": actual})
    return pd.DataFrame(rows)


def test_fit_recovers_exact_linear_relationship() -> None:
    forecast = pd.Series([1000.0, 2000.0, 3000.0, 4000.0])
    cal = fit(forecast, 500 + 0.8 * forecast)
    assert cal.slope == pytest.approx(0.8)
    assert cal.intercept == pytest.approx(500)
    assert cal.residual_quantiles == pytest.approx((0, 0, 0), abs=1e-6)


def test_predict_adds_residual_quantiles_and_clips_at_zero() -> None:
    cal = Calibration(intercept=-100.0, slope=1.0, residual_quantiles=(-50.0, 0.0, 50.0))
    band = cal.predict(pd.Series([100.0, 1000.0]))
    assert list(band.columns) == ["p10_mw", "p50_mw", "p90_mw"]
    assert band.loc[0].tolist() == [0.0, 0.0, 50.0]
    assert band.loc[1].tolist() == [850.0, 900.0, 950.0]


def test_a_days_own_actuals_never_affect_its_values() -> None:
    hours = _hours()
    shocked = hours.copy()
    is_day_3 = shocked["delivery_day"] == DAY_3
    shocked.loc[is_day_3, "actual_mw"] *= 10
    before, after = leave_one_day_out(hours), leave_one_day_out(shocked)
    pd.testing.assert_frame_equal(before[is_day_3], after[is_day_3])
    assert not before[~is_day_3].equals(after[~is_day_3])


def test_hours_without_actual_still_get_a_band() -> None:
    hours = _hours()
    hours.loc[0, "actual_mw"] = np.nan
    assert leave_one_day_out(hours).loc[0].notna().all()


def test_hours_without_forecast_get_no_band() -> None:
    hours = _hours()
    hours.loc[0, "forecast_mw"] = np.nan
    band = leave_one_day_out(hours)
    assert band.loc[0].isna().all()
    assert band.loc[1:].notna().all().all()
