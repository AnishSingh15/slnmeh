"""Fetch the pilot-window wind data from Elexon BMRS and write the snapshot.

Usage (from backend/):  uv run python -m winddesk.ingest [--out PATH]
"""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from winddesk.config import FIRST_DELIVERY_DAY, LAST_DELIVERY_DAY, UK_TZ, Settings
from winddesk.domain.delivery import delivery_window
from winddesk.ingest.elexon import BASE_URL, ElexonClient, iso_utc
from winddesk.repository import write_snapshot

log = logging.getLogger("winddesk.ingest")

# WINDFOR runs reach ~66 h ahead, so runs from three days before the window can cover it.
FORECAST_LOOKBACK = timedelta(days=3)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fetch Elexon wind data into the snapshot.")
    parser.add_argument("--out", type=Path, default=Settings().data_dir)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    window_start, _ = delivery_window(FIRST_DELIVERY_DAY)
    _, window_end = delivery_window(LAST_DELIVERY_DAY)
    settlement_from = window_start.astimezone(UK_TZ).date()
    settlement_to = (window_end - timedelta(minutes=30)).astimezone(UK_TZ).date()
    publish_from = datetime.combine(window_start.date() - FORECAST_LOOKBACK, time(0), tzinfo=UTC)
    publish_to = window_end

    client = ElexonClient()
    actuals = client.wind_actuals(settlement_from, settlement_to)
    forecasts = client.wind_forecasts(publish_from, publish_to)
    log.info("Fetched %d actual rows and %d forecast rows", len(actuals), len(forecasts))

    write_snapshot(
        args.out,
        actuals,
        forecasts,
        {
            "fetched_at": iso_utc(datetime.now(UTC)),
            "source": BASE_URL,
            "requests": {
                "FUELHH": {
                    "settlementDateFrom": settlement_from.isoformat(),
                    "settlementDateTo": settlement_to.isoformat(),
                    "fuelType": "WIND",
                },
                "WINDFOR": {
                    "publishDateTimeFrom": iso_utc(publish_from),
                    "publishDateTimeTo": iso_utc(publish_to),
                },
            },
        },
    )
    log.info("Snapshot written to %s", args.out)


if __name__ == "__main__":
    main()
