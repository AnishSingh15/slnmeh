"""Snapshot persistence: the app's single source of data.

The pilot window is historical, so data is ingested once into gzip CSVs plus a manifest
(fetch time, request parameters, row counts and SHA-256 checksums) committed to the repo.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

ACTUALS_FILE = "actuals.csv.gz"
FORECASTS_FILE = "forecasts.csv.gz"
MANIFEST_FILE = "manifest.json"

_TIME_COLUMNS = {ACTUALS_FILE: ["start_time"], FORECASTS_FILE: ["publish_time", "start_time"]}


@dataclass(frozen=True)
class Snapshot:
    actuals: pd.DataFrame  # start_time, settlement_date, settlement_period, generation_mw
    forecasts: pd.DataFrame  # publish_time, start_time, generation_mw
    manifest: dict[str, Any]


def write_snapshot(
    directory: Path, actuals: pd.DataFrame, forecasts: pd.DataFrame, manifest: dict[str, Any]
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    for name, frame in ((ACTUALS_FILE, actuals), (FORECASTS_FILE, forecasts)):
        out = frame.copy()
        for column in _TIME_COLUMNS[name]:
            out[column] = out[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        path = directory / name
        # mtime=0 keeps the gzip bytes (and so the checksum) identical across runs.
        out.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
        files[name] = {"rows": len(frame), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    content = {**manifest, "files": files}
    (directory / MANIFEST_FILE).write_text(json.dumps(content, indent=2) + "\n")


def load_snapshot(directory: Path) -> Snapshot:
    frames = {}
    for name, time_columns in _TIME_COLUMNS.items():
        frame = pd.read_csv(directory / name, dtype={"settlement_date": str})
        for column in time_columns:
            frame[column] = pd.to_datetime(frame[column], utc=True)
        frames[name] = frame
    manifest = json.loads((directory / MANIFEST_FILE).read_text())
    return Snapshot(
        actuals=frames[ACTUALS_FILE], forecasts=frames[FORECASTS_FILE], manifest=manifest
    )
