import type { AuctionInfo, Meta } from "../api/client";

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
