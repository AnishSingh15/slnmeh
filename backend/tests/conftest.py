"""Synthetic snapshot: 3 delivery days (2-4 Jan 2026) with five runs per day.

Each run's forecast = hourly actual + 1000 + publish hour, so a test can tell which run
was selected (07:30 run -> +1007, 09:30 -> +1009, 15:30 -> +1015).
"""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from winddesk.repository import Snapshot
from winddesk.service import WindDeskService

FIRST_DAY = date(2026, 1, 2)
LAST_DAY = date(2026, 1, 4)
RUN_HOURS = (2, 7, 9, 15, 22)


def make_snapshot() -> Snapshot:
    half_hours = pd.date_range("2026-01-01T00:00Z", "2026-01-04T23:30Z", freq="30min")
    slot = np.arange(len(half_hours)) % 48
    actuals = pd.DataFrame(
        {
            "start_time": half_hours,
            "settlement_date": half_hours.strftime("%Y-%m-%d"),
            "settlement_period": slot + 1,
            "generation_mw": (5000 + 100 * slot).astype(float),
        }
    )
    hourly = actuals.set_index("start_time")["generation_mw"].groupby(lambda t: t.floor("h")).mean()
    rows = []
    for day in pd.date_range("2025-12-31", "2026-01-04", freq="D", tz="UTC"):
        for hour in RUN_HOURS:
            published = day + pd.Timedelta(hours=hour, minutes=30)
            for k in range(-1, 49):  # k <= 0 gives points before publish (not forecasts)
                target = published.floor("h") + pd.Timedelta(hours=k)
                rows.append((published, target, hourly.get(target, 6000.0) + 1000 + hour))
    forecasts = pd.DataFrame(rows, columns=["publish_time", "start_time", "generation_mw"])
    manifest = {"fetched_at": "2026-10-26T12:00:00Z", "source": "synthetic"}
    return Snapshot(actuals=actuals, forecasts=forecasts, manifest=manifest)


@pytest.fixture(scope="session")
def service() -> WindDeskService:
    return WindDeskService(make_snapshot(), first_day=FIRST_DAY, last_day=LAST_DAY)
