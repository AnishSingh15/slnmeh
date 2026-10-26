"""Application service: builds per-auction datasets once, then assembles API view models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from winddesk.api import schemas as s
from winddesk.config import (
    AUCTIONS,
    DEFAULT_AUCTION_ID,
    FIRST_DELIVERY_DAY,
    LAST_DELIVERY_DAY,
    MAX_LEAD_HOURS,
    UK_TZ,
    Auction,
    AuctionId,
)
from winddesk.domain.alignment import hourly_actuals
from winddesk.domain.calibration import Calibration, fit, leave_one_day_out
from winddesk.domain.delivery import (
    decision_cutoff,
    delivery_day_of,
    delivery_days,
    delivery_window,
)
from winddesk.domain.metrics import ErrorSummary, forecast_level_bins, grouped_errors, summarise
from winddesk.domain.selection import fixed_lead, latest_available, runs_between, valid_points
from winddesk.repository import Snapshot


class OutOfWindowError(ValueError):
    """A requested day or range lies outside the pilot window."""


@dataclass(frozen=True)
class AuctionDataset:
    """Decision-time forecasts for one auction over the pilot window.

    `hours` is indexed by target start_time (UTC) with columns delivery_day, publish_time,
    lead_hours, forecast_mw, actual_mw, error_mw and the leave-one-day-out band
    p10_mw / p50_mw / p90_mw. `calibration` is fitted on all days and shown for reference.
    """

    auction: Auction
    hours: pd.DataFrame
    calibration: Calibration


class WindDeskService:
    def __init__(
        self,
        snapshot: Snapshot,
        first_day: date = FIRST_DELIVERY_DAY,
        last_day: date = LAST_DELIVERY_DAY,
    ) -> None:
        self.snapshot = snapshot
        self.days = delivery_days(first_day, last_day)
        self.window_start = pd.Timestamp(delivery_window(first_day)[0])
        self.window_end = pd.Timestamp(delivery_window(last_day)[1])
        self.targets = pd.date_range(
            self.window_start, self.window_end, freq="h", inclusive="left", name="start_time"
        )
        self.target_days = pd.Series([delivery_day_of(t) for t in self.targets], index=self.targets)
        starts = snapshot.actuals["start_time"]
        self.actuals = snapshot.actuals.loc[
            (starts >= self.window_start) & (starts < self.window_end)
        ]
        self.actual_hourly = hourly_actuals(self.actuals)
        self.datasets = {auction_id: self._build(a) for auction_id, a in AUCTIONS.items()}
        self.lead_profile = self._lead_profile()

    # ----- dataset construction -------------------------------------------------------

    def _build(self, auction: Auction) -> AuctionDataset:
        cutoff_by_day = {day: decision_cutoff(day, auction) for day in self.days}
        cutoffs = pd.to_datetime(self.target_days.map(cutoff_by_day), utc=True)
        chosen = latest_available(self.snapshot.forecasts, cutoffs)
        hours = (
            pd.DataFrame({"delivery_day": self.target_days}).join(chosen).join(self.actual_hourly)
        )
        hours["error_mw"] = hours["forecast_mw"] - hours["actual_mw"]
        hours = hours.join(leave_one_day_out(hours))
        pairs = hours.dropna(subset=["forecast_mw", "actual_mw"])
        return AuctionDataset(auction, hours, fit(pairs["forecast_mw"], pairs["actual_mw"]))

    def _lead_profile(self) -> pd.DataFrame:
        """MAE and bias by 1-hour lead-time bin over every valid point for pilot hours."""
        valid = valid_points(self.snapshot.forecasts)
        valid = valid.loc[valid["start_time"].isin(self.actual_hourly.index)]
        lead = ((valid["start_time"] - valid["publish_time"]).dt.total_seconds() / 3600).to_numpy()
        keep = lead <= MAX_LEAD_HOURS
        actual = self.actual_hourly.reindex(valid["start_time"]).to_numpy()
        error = valid["generation_mw"].to_numpy() - actual
        bins = np.minimum(np.floor(lead), MAX_LEAD_HOURS - 1).astype(int)
        return grouped_errors(pd.Series(error[keep]), pd.Series(bins[keep]))

    # ----- view models -------------------------------------------------------------------

    def health(self) -> s.HealthResponse:
        return s.HealthResponse(status="ok", data_fetched_at=self._fetched_at())

    def meta(self) -> s.MetaResponse:
        forecasts = self.snapshot.forecasts
        expected = int((self.window_end - self.window_start) / pd.Timedelta(minutes=30))
        return s.MetaResponse(
            auctions=[_auction_info(a) for a in AUCTIONS.values()],
            default_auction=DEFAULT_AUCTION_ID,
            delivery_days=self.days,
            window_start=self.window_start,
            window_end=self.window_end,
            data=s.DataInfo(
                fetched_at=self._fetched_at(),
                source=str(self.snapshot.manifest.get("source", "")),
                actual_half_hours_expected=expected,
                actual_half_hours_present=len(self.actuals),
                forecast_rows=len(forecasts),
                forecast_rows_valid=len(valid_points(forecasts)),
                forecast_runs=int(forecasts["publish_time"].nunique()),
            ),
        )

    def delivery_day(self, day: date, auction_id: AuctionId) -> s.DeliveryDayResponse:
        self._check_day(day)
        dataset = self.datasets[auction_id]
        start, end = (pd.Timestamp(t) for t in delivery_window(day))
        cutoff = pd.Timestamp(decision_cutoff(day, dataset.auction))
        hours = dataset.hours.loc[(dataset.hours.index >= start) & (dataset.hours.index < end)]
        actual_starts = self.actuals["start_time"]
        actuals = self.actuals.loc[(actual_starts >= start) & (actual_starts < end)]
        later = runs_between(self.snapshot.forecasts, cutoff, start, start, end)
        return s.DeliveryDayResponse(
            delivery_day=day,
            auction=_auction_info(dataset.auction),
            window_start=start,
            window_end=end,
            decision=s.Decision(
                cutoff=cutoff,
                runs_used=sorted(hours["publish_time"].dropna().unique()),
                lead_hours_min=_num(hours["lead_hours"].min(), 2),
                lead_hours_max=_num(hours["lead_hours"].max(), 2),
            ),
            hours=[
                s.HourRow(
                    start_time=row.Index,
                    forecast_mw=_num(row.forecast_mw),
                    p10_mw=_num(row.p10_mw),
                    p50_mw=_num(row.p50_mw),
                    p90_mw=_num(row.p90_mw),
                    actual_mw=_num(row.actual_mw),
                    error_mw=_num(row.error_mw),
                )
                for row in hours.itertuples()
            ],
            actuals_half_hourly=_points(actuals),
            later_runs=[
                s.Run(publish_time=published, points=_points(run))
                for published, run in later.groupby("publish_time")
            ],
            summary=_day_summary(hours),
        )

    def accuracy(self, auction_id: AuctionId) -> s.AccuracyResponse:
        dataset = self.datasets[auction_id]
        hours = dataset.hours
        paired = hours.dropna(subset=["forecast_mw", "actual_mw"])
        inside = (paired["actual_mw"] >= paired["p10_mw"]) & (
            paired["actual_mw"] <= paired["p90_mw"]
        )
        local_hour = pd.Series(
            pd.DatetimeIndex(paired.index).tz_convert(UK_TZ).hour, index=paired.index
        )
        cal = dataset.calibration
        return s.AccuracyResponse(
            auction=_auction_info(dataset.auction),
            raw=_summary(summarise(hours["forecast_mw"], hours["actual_mw"])),
            calibrated=_summary(summarise(hours["p50_mw"], hours["actual_mw"])),
            band_coverage=round(float(inside.mean()), 4),
            calibration=s.CalibrationInfo(
                intercept_mw=round(cal.intercept, 1),
                slope=round(cal.slope, 4),
                p10_offset_mw=round(cal.residual_quantiles[0], 1),
                p50_offset_mw=round(cal.residual_quantiles[1], 1),
                p90_offset_mw=round(cal.residual_quantiles[2], 1),
            ),
            decision_lead_hours_min=round(float(paired["lead_hours"].min()), 2),
            decision_lead_hours_max=round(float(paired["lead_hours"].max()), 2),
            by_lead_time=_group_stats(self.lead_profile),
            by_hour=_group_stats(grouped_errors(paired["error_mw"], local_hour)),
            by_level=_group_stats(
                grouped_errors(paired["error_mw"], forecast_level_bins(paired["forecast_mw"]))
            ),
            daily=_group_stats(
                grouped_errors(paired["error_mw"], paired["delivery_day"].astype(str))
            ),
            series=[
                s.SeriesRow(
                    start_time=row.Index,
                    forecast_mw=_num(row.forecast_mw),
                    p50_mw=_num(row.p50_mw),
                    actual_mw=_num(row.actual_mw),
                )
                for row in hours.itertuples()
            ],
        )

    def lead_time(self, start: date, end: date, hours_ahead: int) -> s.LeadTimeResponse:
        self._check_day(start)
        self._check_day(end)
        if start > end:
            raise OutOfWindowError("start must be on or before end")
        range_start = pd.Timestamp(delivery_window(start)[0])
        range_end = pd.Timestamp(delivery_window(end)[1])
        targets = self.targets[(self.targets >= range_start) & (self.targets < range_end)]
        chosen = fixed_lead(self.snapshot.forecasts, targets, hours_ahead, MAX_LEAD_HOURS)
        frame = pd.DataFrame(index=targets).join(chosen).join(self.actual_hourly)
        has_pairs = bool(frame[["forecast_mw", "actual_mw"]].notna().all(axis=1).any())
        return s.LeadTimeResponse(
            hours_ahead=hours_ahead,
            start=start,
            end=end,
            points=[
                s.LeadTimePoint(
                    start_time=row.Index,
                    forecast_mw=_num(row.forecast_mw),
                    publish_time=None if pd.isna(row.publish_time) else row.publish_time,
                    actual_mw=_num(row.actual_mw),
                )
                for row in frame.itertuples()
            ],
            summary=_summary(summarise(frame["forecast_mw"], frame["actual_mw"]))
            if has_pairs
            else None,
        )

    # ----- helpers -----------------------------------------------------------------------

    def _check_day(self, day: date) -> None:
        if day not in self.days:
            raise OutOfWindowError(
                f"{day} is outside the pilot window ({self.days[0]} to {self.days[-1]})"
            )

    def _fetched_at(self) -> str:
        return str(self.snapshot.manifest.get("fetched_at", "unknown"))


def _num(value: Any, digits: int = 1) -> float | None:
    return None if pd.isna(value) else round(float(value), digits)


def _points(frame: pd.DataFrame) -> list[s.Point]:
    return [
        s.Point(start_time=t, mw=round(float(v), 1))
        for t, v in zip(frame["start_time"], frame["generation_mw"], strict=True)
    ]


def _auction_info(auction: Auction) -> s.AuctionInfo:
    return s.AuctionInfo(
        id=auction.id,
        label=auction.label,
        venue=auction.venue,
        gate_closure=auction.gate_closure.strftime("%H:%M"),
        product_minutes=auction.product_minutes,
    )


def _summary(summary: ErrorSummary) -> s.ErrorSummaryModel:
    return s.ErrorSummaryModel(
        n=summary.n,
        mae_mw=round(summary.mae_mw, 1),
        rmse_mw=round(summary.rmse_mw, 1),
        bias_mw=round(summary.bias_mw, 1),
        nmae=round(summary.nmae, 4),
        p90_abs_error_mw=round(summary.p90_abs_error_mw, 1),
        share_over_forecast=round(summary.share_over_forecast, 4),
    )


def _group_stats(frame: pd.DataFrame) -> list[s.GroupStat]:
    return [
        s.GroupStat(
            key=str(key),
            n=int(row["n"]),
            mae_mw=round(float(row["mae_mw"]), 1),
            bias_mw=round(float(row["bias_mw"]), 1),
        )
        for key, row in frame.iterrows()
    ]


def _day_summary(hours: pd.DataFrame) -> s.DaySummary | None:
    pairs = hours.dropna(subset=["forecast_mw", "actual_mw"])
    if pairs.empty:
        return None
    forecast_gwh = float(pairs["forecast_mw"].sum()) / 1000  # hourly MW == MWh
    actual_gwh = float(pairs["actual_mw"].sum()) / 1000
    error = pairs["error_mw"]
    worst = error.abs().idxmax()
    return s.DaySummary(
        hours_compared=len(pairs),
        forecast_gwh=round(forecast_gwh, 2),
        actual_gwh=round(actual_gwh, 2),
        error_gwh=round(forecast_gwh - actual_gwh, 2),
        error_pct=round((forecast_gwh - actual_gwh) / actual_gwh * 100, 1) if actual_gwh else 0.0,
        mae_mw=round(float(error.abs().mean()), 1),
        largest_miss_mw=round(float(error[worst]), 1),
        largest_miss_at=worst,
    )
