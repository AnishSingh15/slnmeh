"""Linear calibration of the forecast plus empirical residual quantiles.

actual ~ intercept + slope * forecast. The P10 / P50 / P90 planning values add the 10th /
50th / 90th percentile of the fit residuals and are clipped at 0 MW.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

QUANTILES = (0.1, 0.5, 0.9)
BAND_COLUMNS = ("p10_mw", "p50_mw", "p90_mw")


@dataclass(frozen=True)
class Calibration:
    intercept: float
    slope: float
    residual_quantiles: tuple[float, float, float]

    def predict(self, forecast: pd.Series) -> pd.DataFrame:
        base = self.intercept + self.slope * forecast
        return pd.DataFrame(
            {
                column: (base + offset).clip(lower=0)
                for column, offset in zip(BAND_COLUMNS, self.residual_quantiles, strict=True)
            },
            index=forecast.index,
        )


def fit(forecast: pd.Series, actual: pd.Series) -> Calibration:
    if len(forecast) < 2:
        raise ValueError("need at least two hours to calibrate")
    x = forecast.to_numpy(dtype=float)
    y = actual.to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, deg=1)
    residuals = y - (intercept + slope * x)
    p10, p50, p90 = (float(np.quantile(residuals, q)) for q in QUANTILES)
    return Calibration(float(intercept), float(slope), (p10, p50, p90))


def leave_one_day_out(hours: pd.DataFrame) -> pd.DataFrame:
    """Band values for each row of `hours`, each fitted on all *other* delivery days.

    Needs columns delivery_day, forecast_mw and actual_mw. Rows missing an actual still get
    values (they are just not used for fitting); rows missing a forecast get none.
    """
    pairs = hours.dropna(subset=["forecast_mw", "actual_mw"])
    parts = []
    for day, day_rows in hours.dropna(subset=["forecast_mw"]).groupby("delivery_day"):
        train = pairs.loc[pairs["delivery_day"] != day]
        parts.append(fit(train["forecast_mw"], train["actual_mw"]).predict(day_rows["forecast_mw"]))
    if not parts:
        return pd.DataFrame(index=hours.index, columns=list(BAND_COLUMNS), dtype=float)
    return pd.concat(parts).reindex(hours.index)
