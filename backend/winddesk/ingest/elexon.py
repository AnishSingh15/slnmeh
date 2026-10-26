"""Client for the Elexon BMRS Insights API stream endpoints used by WindDesk."""

from __future__ import annotations

import logging
import time
from datetime import UTC, date, datetime
from typing import Any

import httpx
import pandas as pd

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

_ACTUAL_FIELDS = ["startTime", "settlementDate", "settlementPeriod", "fuelType", "generation"]
_FORECAST_FIELDS = ["publishTime", "startTime", "generation"]

log = logging.getLogger(__name__)


class ElexonError(RuntimeError):
    """The BMRS API could not be read or returned unexpected data."""


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class ElexonClient:
    def __init__(
        self, client: httpx.Client | None = None, retries: int = 3, backoff_seconds: float = 1.0
    ) -> None:
        self._client = client or httpx.Client(base_url=BASE_URL, timeout=60.0)
        self._retries = retries
        self._backoff = backoff_seconds

    def wind_actuals(self, settlement_from: date, settlement_to: date) -> pd.DataFrame:
        """Half-hourly wind outturn (FUELHH, fuelType WIND) for the settlement dates."""
        rows = self._get(
            "/datasets/FUELHH/stream",
            {
                "settlementDateFrom": settlement_from.isoformat(),
                "settlementDateTo": settlement_to.isoformat(),
                "fuelType": "WIND",
            },
            _ACTUAL_FIELDS,
        )
        raw = pd.DataFrame(rows, columns=_ACTUAL_FIELDS)
        raw = raw.loc[raw["fuelType"] == "WIND"]
        frame = pd.DataFrame(
            {
                "start_time": pd.to_datetime(raw["startTime"], utc=True),
                "settlement_date": raw["settlementDate"].astype(str),
                "settlement_period": raw["settlementPeriod"].astype(int),
                "generation_mw": raw["generation"].astype(float),
            }
        )
        return _dedupe(frame, ["start_time"], "FUELHH")

    def wind_forecasts(self, publish_from: datetime, publish_to: datetime) -> pd.DataFrame:
        """Every WINDFOR point from runs published in [publish_from, publish_to]."""
        rows = self._get(
            "/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": iso_utc(publish_from),
                "publishDateTimeTo": iso_utc(publish_to),
            },
            _FORECAST_FIELDS,
        )
        raw = pd.DataFrame(rows, columns=_FORECAST_FIELDS)
        frame = pd.DataFrame(
            {
                "publish_time": pd.to_datetime(raw["publishTime"], utc=True),
                "start_time": pd.to_datetime(raw["startTime"], utc=True),
                "generation_mw": raw["generation"].astype(float),
            }
        )
        return _dedupe(frame, ["publish_time", "start_time"], "WINDFOR")

    def _get(self, path: str, params: dict[str, str], fields: list[str]) -> list[dict[str, Any]]:
        response: httpx.Response | None = None
        for attempt in range(1, self._retries + 1):
            try:
                response = self._client.get(path, params=params)
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise ElexonError(f"{path}: HTTP {exc.response.status_code}") from exc
                self._retry_or_raise(path, attempt, exc)
            except httpx.TransportError as exc:
                self._retry_or_raise(path, attempt, exc)
        assert response is not None
        payload = response.json()
        if not isinstance(payload, list):
            raise ElexonError(f"{path}: expected a JSON list, got {type(payload).__name__}")
        for index, row in enumerate(payload):
            missing = [field for field in fields if field not in row]
            if missing:
                raise ElexonError(f"{path}: row {index} missing {missing}")
        return payload

    def _retry_or_raise(self, path: str, attempt: int, exc: Exception) -> None:
        if attempt == self._retries:
            raise ElexonError(f"{path}: failed after {attempt} attempts: {exc}") from exc
        log.warning("%s attempt %d failed (%s); retrying", path, attempt, exc)
        time.sleep(self._backoff * 2 ** (attempt - 1))


def _dedupe(frame: pd.DataFrame, keys: list[str], dataset: str) -> pd.DataFrame:
    deduped = frame.drop_duplicates(keys, keep="last")
    if dropped := len(frame) - len(deduped):
        log.warning("%s: dropped %d duplicate rows", dataset, dropped)
    return deduped.sort_values(keys).reset_index(drop=True)
