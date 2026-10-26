"""API response models. The frontend's TypeScript types are generated from these."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from winddesk.config import AuctionId


class AuctionInfo(BaseModel):
    id: AuctionId
    label: str
    venue: str
    gate_closure: str  # "HH:MM", UK local time on the day before delivery
    product_minutes: int


class DataInfo(BaseModel):
    fetched_at: str
    source: str
    actual_half_hours_expected: int
    actual_half_hours_present: int
    forecast_rows: int
    forecast_rows_valid: int
    forecast_runs: int


class MetaResponse(BaseModel):
    auctions: list[AuctionInfo]
    default_auction: AuctionId
    delivery_days: list[date]
    window_start: datetime
    window_end: datetime
    data: DataInfo


class HealthResponse(BaseModel):
    status: str
    data_fetched_at: str


class Point(BaseModel):
    start_time: datetime
    mw: float


class Run(BaseModel):
    publish_time: datetime
    points: list[Point]


class HourRow(BaseModel):
    start_time: datetime
    forecast_mw: float | None
    p10_mw: float | None
    p50_mw: float | None
    p90_mw: float | None
    actual_mw: float | None
    error_mw: float | None


class Decision(BaseModel):
    cutoff: datetime
    runs_used: list[datetime]
    lead_hours_min: float | None
    lead_hours_max: float | None


class DaySummary(BaseModel):
    hours_compared: int
    forecast_gwh: float
    actual_gwh: float
    error_gwh: float
    error_pct: float
    mae_mw: float
    largest_miss_mw: float  # signed: forecast - actual
    largest_miss_at: datetime


class DeliveryDayResponse(BaseModel):
    delivery_day: date
    auction: AuctionInfo
    window_start: datetime
    window_end: datetime
    decision: Decision
    hours: list[HourRow]
    actuals_half_hourly: list[Point]
    later_runs: list[Run]
    summary: DaySummary | None


class ErrorSummaryModel(BaseModel):
    n: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    nmae: float
    p90_abs_error_mw: float
    share_over_forecast: float


class CalibrationInfo(BaseModel):
    intercept_mw: float
    slope: float
    p10_offset_mw: float
    p50_offset_mw: float
    p90_offset_mw: float


class GroupStat(BaseModel):
    key: str
    n: int
    mae_mw: float
    bias_mw: float


class SeriesRow(BaseModel):
    start_time: datetime
    forecast_mw: float | None
    p50_mw: float | None
    actual_mw: float | None


class AccuracyResponse(BaseModel):
    auction: AuctionInfo
    raw: ErrorSummaryModel
    calibrated: ErrorSummaryModel
    band_coverage: float
    calibration: CalibrationInfo
    decision_lead_hours_min: float
    decision_lead_hours_max: float
    by_lead_time: list[GroupStat]
    by_hour: list[GroupStat]
    by_level: list[GroupStat]
    daily: list[GroupStat]
    series: list[SeriesRow]


class LeadTimePoint(BaseModel):
    start_time: datetime
    forecast_mw: float | None
    publish_time: datetime | None
    actual_mw: float | None


class LeadTimeResponse(BaseModel):
    hours_ahead: int
    start: date
    end: date
    points: list[LeadTimePoint]
    summary: ErrorSummaryModel | None
