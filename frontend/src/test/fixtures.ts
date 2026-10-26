import type { AuctionInfo, DeliveryDay, Meta } from "../api/client";

export const epex: AuctionInfo = {
  id: "epex_60",
  label: "EPEX GB Day-Ahead 60-min",
  venue: "EPEX SPOT",
  gate_closure: "09:20",
  product_minutes: 60,
};

export const meta: Meta = {
  auctions: [
    epex,
    {
      id: "n2ex_60",
      label: "N2EX GB Day-Ahead hourly",
      venue: "Nord Pool",
      gate_closure: "09:50",
      product_minutes: 60,
    },
  ],
  default_auction: "epex_60",
  delivery_days: ["2026-01-02", "2026-01-03"],
  window_start: "2026-01-01T23:00:00Z",
  window_end: "2026-01-03T23:00:00Z",
  data: {
    fetched_at: "2026-10-26T12:00:00Z",
    source: "https://data.elexon.co.uk/bmrs/api/v1",
    actual_half_hours_expected: 96,
    actual_half_hours_present: 96,
    forecast_rows: 1000,
    forecast_rows_valid: 900,
    forecast_runs: 20,
  },
};

export const deliveryDay: DeliveryDay = {
  delivery_day: "2026-01-02",
  auction: epex,
  window_start: "2026-01-01T23:00:00Z",
  window_end: "2026-01-02T23:00:00Z",
  decision: {
    cutoff: "2026-01-01T09:20:00Z",
    runs_used: ["2026-01-01T07:30:00Z"],
    lead_hours_min: 15.5,
    lead_hours_max: 16.5,
  },
  hours: [
    {
      start_time: "2026-01-01T23:00:00Z",
      forecast_mw: 12000,
      p10_mw: 8000,
      p50_mw: 10500,
      p90_mw: 12500,
      actual_mw: 10000,
      error_mw: 2000,
    },
    {
      start_time: "2026-01-02T00:00:00Z",
      forecast_mw: 11000,
      p10_mw: 7500,
      p50_mw: 9700,
      p90_mw: 11800,
      actual_mw: 10500,
      error_mw: 500,
    },
  ],
  actuals_half_hourly: [
    { start_time: "2026-01-01T23:00:00Z", mw: 9900 },
    { start_time: "2026-01-01T23:30:00Z", mw: 10100 },
    { start_time: "2026-01-02T00:00:00Z", mw: 10400 },
    { start_time: "2026-01-02T00:30:00Z", mw: 10600 },
  ],
  later_runs: [
    {
      publish_time: "2026-01-01T15:30:00Z",
      points: [
        { start_time: "2026-01-01T23:00:00Z", mw: 11000 },
        { start_time: "2026-01-02T00:00:00Z", mw: 10800 },
      ],
    },
  ],
  summary: {
    hours_compared: 2,
    forecast_gwh: 23,
    actual_gwh: 20.5,
    error_gwh: 2.5,
    error_pct: 12.2,
    mae_mw: 1250,
    largest_miss_mw: 2000,
    largest_miss_at: "2026-01-01T23:00:00Z",
  },
};
