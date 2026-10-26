import type { ReactNode } from "react";
import type { Meta } from "../../api/client";
import { Card } from "../../components/Card";
import { formatUkDayTime } from "../../lib/format";

const Prose = ({ children }: { children: ReactNode }) => (
  <div className="space-y-2 text-sm leading-relaxed text-slate-700">{children}</div>
);

export function MethodPanel({ meta }: { meta: Meta }) {
  const data = meta.data;
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="What this pilot covers">
        <Prose>
          <p>
            National GB wind generation from transmission-metered wind farms, using two Elexon BMRS
            datasets only: <b>FUELHH</b> (half-hourly outturn, fuel type WIND) and <b>WINDFOR</b>{" "}
            (NESO's hourly wind forecast, published about eight times a day).
          </p>
          <p>
            Scope is <b>purchase decisions made in January 2026</b>: day-ahead auctions held 1–31
            January, which deliver power from 2 January to 1 February 2026.
          </p>
        </Prose>
      </Card>

      <Card title="When the decision is made">
        <Prose>
          <p>
            The deadline is the gate closure of the day-ahead auction you trade in, in UK time on
            the day before delivery. Choose it with the Auction selector; every view follows it.
          </p>
        </Prose>
        <table className="mt-3 w-full text-left text-sm">
          <thead className="text-xs text-slate-500">
            <tr>
              <th className="py-1 font-medium">Auction</th>
              <th className="py-1 font-medium">Gate closure (D−1)</th>
              <th className="py-1 font-medium">Products</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {meta.auctions.map((auction) => (
              <tr key={auction.id}>
                <td className="py-1.5">{auction.label}</td>
                <td className="py-1.5 tabular-nums">{auction.gate_closure}</td>
                <td className="py-1.5">{auction.product_minutes}-minute</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Delivery day">
        <Prose>
          <p>
            As in the GB day-ahead auctions, delivery day D runs from{" "}
            <b>23:00 UK time on D−1 to 23:00 on D</b> (23 or 25 hours on clock-change days).
          </p>
        </Prose>
      </Card>

      <Card title="Which forecast you had">
        <Prose>
          <p>
            For every hour of delivery day D we use the forecast from the{" "}
            <b>latest WINDFOR run published at or before gate closure on D−1</b>. Runs published
            later are never used for the decision; they appear only as "later runs", to show what
            was learned after committing.
          </p>
          <p>
            WINDFOR runs also contain values for hours before their own publish time. Those are not
            forecasts and are excluded.
          </p>
        </Prose>
      </Card>

      <Card title="Comparing like with like">
        <Prose>
          <p>
            Forecasts are hourly and outturn is half-hourly, so each hour's actual is the mean of
            its two half-hours, which matches hourly auction products. An hour missing a half-hour
            is left out: gaps are never filled. Error = forecast − actual, so a positive error means
            the forecast was too high.
          </p>
        </Prose>
      </Card>

      <Card title="Calibrated forecast and band">
        <Prose>
          <p>
            Actual wind is fitted as a straight line of the forecast (actual ≈ a + b × forecast).
            Adding the 10th, 50th and 90th percentiles of that fit's misses gives the{" "}
            <b>Low case (P10)</b>, <b>Expected (P50)</b> and <b>High case (P90)</b>. P10 reads: "in
            comparable hours, actual wind came in below this one time in ten".
          </p>
          <p>
            Values shown for a day are fitted only on the <b>other</b> days, so every calibrated
            number is out-of-sample for the day it describes.
          </p>
        </Prose>
      </Card>

      <Card title="Caveats">
        <Prose>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              31 days of one winter month: calibration and band figures are indicative. In
              production the calibration would roll forward on past days only, over a longer
              history.
            </li>
            <li>
              The over-forecast grows on windy days. That fits transmission-constraint curtailment
              (metered output held below what the wind could produce), a hypothesis to confirm with
              NESO.
            </li>
            <li>
              A run's publish time is treated as when it became available; spot checks found runs
              retrievable within minutes of their publish time.
            </li>
            <li>
              The 30-minute auction trades half-hours, but the forecast is hourly, so evaluation is
              hourly.
            </li>
            <li>Embedded (distribution-connected) wind and demand are outside the data scope.</li>
          </ul>
        </Prose>
      </Card>

      <Card title="Data">
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
          <dt className="text-slate-500">Snapshot fetched</dt>
          <dd>{formatUkDayTime(data.fetched_at)} UK</dd>
          <dt className="text-slate-500">Source</dt>
          <dd className="break-all">{data.source}</dd>
          <dt className="text-slate-500">Half-hours of outturn</dt>
          <dd className="tabular-nums">
            {data.actual_half_hours_present} of {data.actual_half_hours_expected}
          </dd>
          <dt className="text-slate-500">Forecast runs</dt>
          <dd className="tabular-nums">{data.forecast_runs}</dd>
          <dt className="text-slate-500">Forecast values</dt>
          <dd className="tabular-nums">
            {data.forecast_rows.toLocaleString("en-GB")} (
            {data.forecast_rows_valid.toLocaleString("en-GB")} valid forecasts)
          </dd>
        </dl>
        <p className="mt-3 text-xs text-slate-500">
          Docs:{" "}
          <a
            className="underline"
            href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream"
          >
            FUELHH
          </a>{" "}
          ·{" "}
          <a
            className="underline"
            href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream"
          >
            WINDFOR
          </a>
        </p>
      </Card>
    </div>
  );
}
