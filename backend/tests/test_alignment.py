import pandas as pd

from winddesk.domain.alignment import hourly_actuals


def test_hourly_mean_of_both_half_hours_and_incomplete_hours_dropped() -> None:
    actuals = pd.DataFrame(
        {
            "start_time": pd.to_datetime(
                ["2026-01-12T00:30Z", "2026-01-12T00:00Z", "2026-01-12T01:00Z"], utc=True
            ),
            "generation_mw": [200.0, 100.0, 300.0],
        }
    )
    hourly = hourly_actuals(actuals)
    assert hourly.name == "actual_mw"
    assert hourly.index.name == "start_time"
    assert hourly.to_dict() == {pd.Timestamp("2026-01-12T00:00Z"): 150.0}
