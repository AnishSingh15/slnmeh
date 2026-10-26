import numpy as np
import pandas as pd
import pytest

from winddesk.domain.metrics import forecast_level_bins, grouped_errors, summarise


def test_summarise_known_values_and_skips_missing() -> None:
    forecast = pd.Series([110.0, 90.0, 130.0, 999.0])
    actual = pd.Series([100.0, 100.0, 100.0, np.nan])
    s = summarise(forecast, actual)
    assert s.n == 3
    assert s.mae_mw == pytest.approx(50 / 3)
    assert s.rmse_mw == pytest.approx((1100 / 3) ** 0.5)
    assert s.bias_mw == pytest.approx(10.0)
    assert s.nmae == pytest.approx(50 / 3 / 100)
    assert s.p90_abs_error_mw == pytest.approx(26.0)
    assert s.share_over_forecast == pytest.approx(2 / 3)


def test_summarise_without_pairs_raises() -> None:
    with pytest.raises(ValueError, match="no hours"):
        summarise(pd.Series([1.0]), pd.Series([np.nan]))


def test_grouped_errors() -> None:
    error = pd.Series([10.0, -10.0, 30.0, -30.0])
    keys = pd.Series(["b", "b", "a", "a"])
    out = grouped_errors(error, keys)
    assert out.index.tolist() == ["a", "b"]
    assert out["n"].tolist() == [2, 2]
    assert out["mae_mw"].tolist() == [30.0, 10.0]
    assert out["bias_mw"].tolist() == [0.0, 0.0]


def test_forecast_level_bins() -> None:
    bins = forecast_level_bins(pd.Series([0.0, 3999.0, 4000.0, 25000.0]))
    assert bins.astype(str).tolist() == ["0-4 GW", "0-4 GW", "4-8 GW", "20+ GW"]
