"""Which forecast value was available for each target hour.

A forecast run is the set of WINDFOR rows sharing one publish_time. Points whose target
hour starts before the run was published are not forecasts and are always excluded.
"""

from __future__ import annotations

import pandas as pd


def valid_points(forecasts: pd.DataFrame) -> pd.DataFrame:
    return forecasts.loc[forecasts["start_time"] >= forecasts["publish_time"]]


def latest_available(forecasts: pd.DataFrame, cutoffs: pd.Series) -> pd.DataFrame:
    """For each target hour, the valid point from the latest run published at or before
    that target's cutoff.

    `cutoffs` is indexed by target start_time with the cutoff instant as value. Returns a
    frame indexed by start_time with publish_time, forecast_mw and lead_hours; targets with
    no eligible run are absent.
    """
    candidates = valid_points(forecasts).merge(
        cutoffs.rename("cutoff"), left_on="start_time", right_index=True
    )
    eligible = candidates.loc[candidates["publish_time"] <= candidates["cutoff"]]
    latest = eligible.loc[eligible.groupby("start_time")["publish_time"].idxmax()]
    chosen = latest.set_index("start_time").sort_index()
    lead = (chosen.index.to_series() - chosen["publish_time"]).dt.total_seconds() / 3600
    return pd.DataFrame(
        {
            "publish_time": chosen["publish_time"],
            "forecast_mw": chosen["generation_mw"],
            "lead_hours": lead,
        }
    )


def fixed_lead(
    forecasts: pd.DataFrame, targets: pd.DatetimeIndex, lead_hours: float, max_lead_hours: float
) -> pd.DataFrame:
    """Latest valid point published at least `lead_hours` before each target, ignoring
    points more than `max_lead_hours` ahead."""
    cutoffs = pd.Series(targets - pd.Timedelta(hours=lead_hours), index=targets)
    chosen = latest_available(forecasts, cutoffs)
    return chosen.loc[chosen["lead_hours"] <= max_lead_hours]


def runs_between(
    forecasts: pd.DataFrame,
    after: pd.Timestamp,
    before: pd.Timestamp,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> pd.DataFrame:
    """Valid points in [window_start, window_end) from runs published strictly between
    `after` and `before`."""
    valid = valid_points(forecasts)
    mask = (
        (valid["publish_time"] > after)
        & (valid["publish_time"] < before)
        & (valid["start_time"] >= window_start)
        & (valid["start_time"] < window_end)
    )
    return valid.loc[mask].sort_values(["publish_time", "start_time"])
