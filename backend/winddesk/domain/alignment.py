"""Align half-hourly outturn with hourly forecasts."""

from __future__ import annotations

import pandas as pd


def hourly_actuals(actuals: pd.DataFrame) -> pd.Series:
    """Hourly mean MW, indexed by hour start (UTC).

    An hour is kept only if both of its half-hours are present: never interpolated.
    The mean of the two half-hours is energy-consistent with hourly auction products.
    """
    half_hourly = actuals.set_index("start_time")["generation_mw"].sort_index()
    by_hour = half_hourly.groupby(pd.DatetimeIndex(half_hourly.index).floor("h"))
    means = by_hour.mean()[by_hour.count() == 2]
    means.index.name = "start_time"
    return means.rename("actual_mw")
