# WindDesk — Design

Day-ahead wind forecast intelligence for a GB electricity supplier's trading desk.

Status: approved for implementation · Last updated: 2026-10-26

---

## 1. Problem

The client is a UK energy supplier. Its day-ahead team buys power in the GB day-ahead
auctions on day D−1 to cover consumer demand on day D that renewable generation will not
meet. Wind output is weather-dependent and the purchase is committed a day ahead, so the
team relies on wind forecasts and needs to:

1. **See the latest wind forecast that was available when the purchase decision had to be made.**
2. **Quantify how accurate that forecast is**, so decisions can account for the error.

**Scope.** National-level GB wind only, using two Elexon BMRS datasets and nothing else:

| Dataset | Endpoint | Fields used |
|---|---|---|
| Actual generation | `/datasets/FUELHH/stream`, `fuelType=WIND` | `startTime` (30-min resolution), `generation` (MW) |
| Forecast generation | `/datasets/WINDFOR/stream` | `startTime`, `publishTime`, `generation` (MW) |

Only data relevant to **purchase decisions made in January 2026** is in scope.

---

## 2. Domain model

### 2.1 Auctions and decision time

The decision deadline is the gate closure of the day-ahead auction the desk trades in.
All times are UK local time (Europe/London).

| Auction id | Venue / product | Gate closure (D−1) | Products |
|---|---|---|---|
| `epex_60` (default) | EPEX SPOT GB Day-Ahead 60-min | 09:20 | Hourly |
| `n2ex_60` | Nord Pool N2EX GB Day-Ahead | 09:50 | Hourly |
| `epex_30` | EPEX SPOT GB Day-Ahead 30-min | 15:30 | Half-hourly |

Sources: EPEX SPOT trading brochure (GB 60-min auction moved to 09:20 GMT); Nord Pool GB
product specification (N2EX gate closure 09:50); Modo Energy GB markets explainer
(EPEX 30-min at 15:30).

`epex_60` is the default because it is the earliest hourly auction: its decision cutoff is
the most conservative of the three.

### 2.2 Definitions

- **Delivery day D** — the auction delivery day: **23:00 UK on D−1 → 23:00 UK on D**
  (EFA-day convention used by the GB day-ahead auctions; 24 hourly products, 23 or 25 on
  clock-change days).
- **Decision cutoff for D** — the selected auction's gate closure on D−1, UK local time.
- **Pilot window** — auctions held 1–31 January 2026, i.e. **delivery days 2 January –
  1 February 2026**, i.e. target hours from `2026-01-01T23:00Z` up to (excluding)
  `2026-02-01T23:00Z`. GB is on GMT throughout, so UK local time equals UTC in this window.
- **Forecast run** — all WINDFOR rows sharing one `publishTime`. In the pilot data there are
  8 runs per day (02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC; one run was
  published late at 12:25 instead of 11:30). Each run has 73 hourly points.
- **Lead time** — `startTime − publishTime` of a forecast point.
- **Valid forecast point** — lead time ≥ 0. WINDFOR runs also contain points for hours
  *before* their publish time (≈4,000 rows in the pilot data); these are not forecasts and
  are excluded.
- **Forecast available at decision time** — for each target hour `t` of delivery day D:
  the valid point for `t` from the run with the greatest `publishTime ≤ cutoff(D)`.
- **Fixed-lead-time forecast** (secondary mode) — for each target hour `t` and a chosen
  `H ∈ [0, 48]` hours: the valid point for `t` from the run with the greatest
  `publishTime ≤ t − H`, considering only points with lead time ≤ 48 h. No point → gap.
- **Hourly actual** — mean of the two half-hourly FUELHH values inside the hour (MW). This
  is energy-consistent with hourly auction products. If either half-hour is missing, the
  hour is excluded, never interpolated.
- **Error** — `forecast − actual` (MW). Positive = over-forecast: wind came in lower than
  forecast, so a desk that trusted the forecast under-bought.

### 2.3 Calibrated forecast and planning band

The raw forecast is shown as published. Alongside it, the app shows a **calibrated
forecast** derived only from the pilot data:

- Fit `actual = a + b · forecast` by ordinary least squares on the decision-time forecast
  pairs; residuals `r = actual − (a + b · forecast)`.
- **Low case (P10)**, **Expected (P50)**, **High case (P90)** =
  `a + b · forecast + quantile(r, 0.10 / 0.50 / 0.90)`, clipped at 0.
  P10 reads as "in comparable hours, actual wind was below this 10% of the time".
- **Leave-one-day-out**: the calibrated values shown for delivery day D are fitted on all
  *other* delivery days, so every calibrated number in the app is out-of-sample for the
  day it describes. Accuracy-page metrics for the calibrated forecast pool these
  out-of-sample predictions.
- Calibration is fitted per auction (each auction selects different runs).

Limitations, stated in the app: 31 days of one winter month is a small sample;
leave-one-day-out uses days after D, so it is cross-validation rather than a strictly causal
backtest. The production design is a rolling calibration on past days only, over a longer
history.

### 2.4 Findings that motivate the design

From the pilot data, auction `epex_60`, 744 delivery hours:

| Measure | Value |
|---|---|
| MAE, forecast available at decision time | ≈ 2.04 GW (mean actual ≈ 11.3 GW) |
| RMSE | ≈ 2.50 GW |
| Bias (forecast − actual) | ≈ +1.75 GW (systematic over-forecast) |
| Bias by forecast level | ≈ +0.8 GW below 6 GW forecast; ≈ +2.5 GW above 14 GW |
| Calibrated P50, leave-one-day-out MAE | ≈ 1.21 GW (≈ 40% lower) |
| P10–P90 band coverage, out-of-sample | ≈ 78% (nominal 80%) |
| MAE by lead time, all runs | ≈ 1.7 GW at 0–4 h → ≈ 2.4 GW at 44–48 h |
| Largest daily MAE (delivery day) | 28 Jan, 12 Jan, 11 Jan |

The over-forecast growing with wind level is consistent with transmission-constraint
curtailment on windy days (metered output below what the wind could produce). This is a
hypothesis to confirm with NESO, presented as such.

The app computes all of these at runtime; a regression test pins them to the snapshot.

---

## 3. Product

Single-page web app. Header: product name, **auction selector** (drives every view), and a
link to the Method & data panel. Tab, auction and date are kept in the URL so every view is
a shareable link.

### 3.1 Delivery day (landing tab)

"What did I know when I had to buy, and how did it turn out?"

- Delivery-day picker (2 Jan – 1 Feb) with previous/next buttons.
- Decision context line: auction gate closure (date/time), run used (publish time),
  lead-time range covered.
- KPI cards: forecast energy (GWh), actual energy (GWh), day error (GWh and % of actual
  energy), MAE (MW), largest hourly miss (MW and hour).
- Chart: actual (half-hourly), decision-time forecast (hourly), calibrated P50 with shaded
  P10–P90 band; toggle **Show later runs** draws, as thin lines, every run published after
  the decision cutoff and before the delivery day starts (23:00 on D−1) — what was learned
  between committing and delivery.
- Hourly table (hour, forecast, P10, P50, P90, actual, error) with CSV export.

### 3.2 Accuracy (whole pilot window)

"How much can I trust the forecast, and how should I adjust for it?"

- Headline metrics, raw vs calibrated side by side: MAE, RMSE, bias, normalised MAE
  (MAE / mean actual), P90 absolute error, share of hours over-forecast; plus P10–P90
  coverage.
- Charts:
  1. Actual vs decision-time forecast across the whole window (zoomable).
  2. MAE and bias vs lead time: all valid points for pilot target hours, 1-hour lead-time
     bins from 0 to 48 h; the lead-time range of the selected auction is shaded.
  3. MAE by hour of day (target hour, UK local time).
  4. MAE and bias by forecast level, 4 GW bins (0–4, 4–8, …, 20+ GW); explains the calibration.
  5. Daily MAE bars; clicking a day opens it in the Delivery day tab.

### 3.3 Lead-time explorer (secondary tab)

Date range within the pilot window plus a 0–48 h slider: actual vs fixed-lead-time forecast
(definition in 2.2), with MAE / RMSE / bias for that lead time. Defaults: whole pilot window,
4 h.

### 3.4 Method & data panel

Plain-language definitions (delivery day, decision cutoff, forecast selection, hourly
alignment, calibration and its validation), assumptions and limitations (section 7), data
completeness counts, snapshot fetch time, and source links.

### 3.5 States

Loading skeletons; error state with retry; missing data rendered as gaps with a note.
Responsive layout: cards stack and charts go full width on mobile.

---

## 4. Architecture

```
Elexon BMRS API ──(ingest CLI)──▶ data/snapshot/{actuals,forecasts}.csv.gz + manifest.json
                                          │ loaded once at startup
                                          ▼
                 FastAPI app ── domain layer (pure functions) ──▶ JSON API (/api/*)
                                          │ same process serves the built frontend
                                          ▼
                 React + TypeScript SPA (Vite, TanStack Query, Recharts, Tailwind)
```

### 4.1 Data

- The pilot window is historical and fixed, so data is ingested once into a versioned
  snapshot committed to the repo. The app is deterministic, fast to start, and does not
  depend on Elexon being reachable. `make ingest` refreshes the snapshot from the live API.
- Ingest ranges: FUELHH settlement dates 2026-01-01 → 2026-02-01; WINDFOR publish times
  2025-12-29T00:00Z → 2026-02-01T23:00Z (covers every run that can reach a pilot target
  hour, plus later runs for the "Show later runs" view).
- The snapshot stores raw normalised rows (no filtering), so every exclusion happens in
  tested domain code and is reported in completeness counts.
- `manifest.json`: fetch timestamp, source URLs and parameters, row counts, SHA-256 per file.

### 4.2 Backend (`backend/winddesk`, Python 3.12, FastAPI, pandas)

| Module | Responsibility |
|---|---|
| `config.py` | Auctions, pilot window, settings (data dir, log level, port) |
| `ingest/elexon.py` | HTTP client for both stream endpoints: retries, timeouts, schema validation |
| `ingest/__main__.py` | `python -m winddesk.ingest` → writes snapshot + manifest |
| `repository.py` | Loads the snapshot into typed DataFrames once |
| `domain/delivery.py` | Delivery-day window and gate-closure instants (zoneinfo, DST-safe) |
| `domain/selection.py` | Forecast available at a cutoff; fixed-lead-time selection; valid-point filter |
| `domain/alignment.py` | Half-hourly actuals → hourly means |
| `domain/calibration.py` | Linear calibration, residual quantiles, leave-one-day-out predictions |
| `domain/metrics.py` | MAE, RMSE, bias, quantiles, breakdowns |
| `service.py` | Builds and caches per-auction datasets at startup; assembles view models |
| `api/schemas.py`, `api/routes.py` | Pydantic response models and routes |
| `main.py` | App factory; mounts the API and serves the built frontend |
| `openapi.py` | Exports the OpenAPI schema used to generate the frontend's TypeScript types |

Domain functions take and return plain data (DataFrames / dataclasses), with no I/O, so they
can be tested in isolation.

### 4.3 API

All endpoints are read-only `GET`. Invalid parameters (unknown auction, date outside the
pilot window, `hours` outside 0–48) return `422` with a clear message.

| Endpoint | Returns |
|---|---|
| `/api/health` | Status and snapshot fetch time |
| `/api/meta` | Auctions, default auction, delivery days, pilot window, data manifest and completeness |
| `/api/delivery-day?date=YYYY-MM-DD&auction=` | Window, decision context (gate closure, run used, lead-time range), hourly rows (forecast, P10, P50, P90, actual, error), half-hourly actuals, later runs, day summary |
| `/api/accuracy?auction=` | Raw and calibrated metrics, band coverage, calibration coefficients, breakdowns by lead time / hour / forecast level / day, window series |
| `/api/lead-time?start=&end=&hours=` | Fixed-lead-time series (forecast, publish time, actual) and metrics |

Responses are gzip-compressed. Per-auction datasets are computed at startup, so requests only
slice cached frames.

### 4.4 Frontend (`frontend/`, React 19, TypeScript 5.9 strict, Vite)

- `src/api/` — typed client; types **generated from the FastAPI OpenAPI schema**
  (`openapi-typescript`) so the contract cannot drift.
- `src/features/{delivery-day,accuracy,lead-time,method}/` — one folder per tab.
- `src/components/` — shared UI (KPI card, chart card, auction selector, states).
- TanStack Query for fetching and caching; URL search params for tab, auction and date.
- Recharts for charts; Tailwind for styling.

---

## 5. Quality

- **Backend tests (pytest)**
  - `delivery`: delivery window and gate closure, including clock-change days.
  - `selection`: never selects a run published after the cutoff; excludes negative-lead
    points; handles a late run and a missing run; fixed-lead-time respects the 48 h cap.
  - `alignment` and `metrics`: hand-computed expected values; missing half-hour excludes the hour.
  - `calibration`: a day's own data never affects its own calibrated values.
  - `api`: TestClient against a small fixture snapshot (shapes, 422s).
  - `ingest`: recorded HTTP responses; no network in tests.
  - Regression: the committed snapshot reproduces the headline numbers in 2.4.
- **Frontend**: TypeScript strict, ESLint, Vitest for formatters, URL state and key components.
- **Tooling**: ruff (lint + format), mypy, `Makefile` targets (`dev`, `test`, `lint`,
  `ingest`, `docker`).
- **CI (GitHub Actions)**: backend lint, types and tests; frontend lint, types, tests and
  build; Docker build plus a smoke test (`/api/health` and the index page).
- Small, conventional commits.

---

## 6. Deployment

- **Dockerfile** (multi-stage): Node stage builds the frontend; slim Python 3.12 stage
  installs the backend, copies the built assets, runs as a non-root user, binds to `$PORT`,
  and has a healthcheck.
- **docker-compose.yml**: local development with backend and frontend hot reload.
- **Heroku** (container stack, `heroku.yml`): deploys the same image. Basic dyno, which does
  not sleep, so the first visit is not a cold start.

---

## 7. Assumptions and limitations

1. `publishTime` is treated as the moment a run became available. Checked on 2026-10-26:
   the run with `publishTime` 11:30Z was retrievable by 11:41Z.
2. A WINDFOR value at `HH:00` represents the hour `HH:00–HH+1:00` and is compared with the
   mean of the two half-hourly actuals. Comparing with the `HH:00` half-hour alone changes
   MAE by under 1%.
3. The 30-min auction trades half-hourly products, but WINDFOR is hourly, so evaluation is
   hourly for every auction.
4. Both datasets cover transmission-metered wind; embedded (distribution-connected) wind and
   demand are outside the data scope.
5. The observed run schedule (02:30, 04:30, … UTC in January 2026) differs from the
   schedule text on the Elexon wind generation page (03:30, 05:30, …); the app uses observed
   publish times.
6. Calibration and band estimates come from 31 days of one winter month and are indicative
   (see 2.3).

---

## 8. Out of scope / next steps

- Scheduled live ingestion into a database; rolling (past-only) calibration over a longer history.
- Net-position view combining wind with the client's demand forecast.
- Solar and other renewables; embedded generation.
- Alerts when a new run moves the forecast materially before gate closure.
- Authentication / SSO for multi-user production use.
