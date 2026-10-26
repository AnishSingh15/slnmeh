"""Forecast accuracy metrics. Error convention: forecast - actual, in MW."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

LEVEL_BIN_EDGES_MW = [0, 4000, 8000, 12000, 16000, 20000, np.inf]
LEVEL_BIN_LABELS = ["0-4 GW", "4-8 GW", "8-12 GW", "12-16 GW", "16-20 GW", "20+ GW"]


@dataclass(frozen=True)
class ErrorSummary:
    n: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    nmae: float  # MAE / mean actual
    p90_abs_error_mw: float
    share_over_forecast: float  # share of hours with forecast above actual


def summarise(forecast: pd.Series, actual: pd.Series) -> ErrorSummary:
    """Summary over the hours where both series have a value."""
    pairs = pd.DataFrame({"forecast": forecast, "actual": actual}).dropna()
    if pairs.empty:
        raise ValueError("no hours with both a forecast and an actual")
    error = pairs["forecast"] - pairs["actual"]
    mae = float(error.abs().mean())
    return ErrorSummary(
        n=len(pairs),
        mae_mw=mae,
        rmse_mw=float(np.sqrt((error**2).mean())),
        bias_mw=float(error.mean()),
        nmae=mae / float(pairs["actual"].mean()),
        p90_abs_error_mw=float(error.abs().quantile(0.9)),
        share_over_forecast=float((error > 0).mean()),
    )


def grouped_errors(error: pd.Series, keys: pd.Series) -> pd.DataFrame:
    """Count, MAE and bias of `error` per key (index-aligned), in key order."""
    frame = pd.DataFrame({"error": error, "key": keys}).dropna()
    frame["abs_error"] = frame["error"].abs()
    return frame.groupby("key", observed=True, sort=True).agg(
        n=("error", "size"), mae_mw=("abs_error", "mean"), bias_mw=("error", "mean")
    )


def forecast_level_bins(forecast: pd.Series) -> pd.Series:
    return pd.cut(forecast, bins=LEVEL_BIN_EDGES_MW, right=False, labels=LEVEL_BIN_LABELS)
