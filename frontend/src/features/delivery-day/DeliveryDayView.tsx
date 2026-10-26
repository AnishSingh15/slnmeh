import { useState } from "react";
import type { AuctionInfo, DeliveryDay, Meta } from "../../api/client";
import { useDeliveryDay } from "../../api/hooks";
import { Card } from "../../components/Card";
import { KpiCard } from "../../components/KpiCard";
import { ErrorState, Loading } from "../../components/States";
import {
  formatDeliveryDay,
  formatHours,
  formatMW,
  formatSignedGW,
  formatUkDayTime,
  formatUkTime,
} from "../../lib/format";
import { useSearchParam } from "../../lib/url-state";
import { DeliveryDayChart } from "./DeliveryDayChart";
import { HourlyTable } from "./HourlyTable";

type Props = { meta: Meta; auction: AuctionInfo };

export function DeliveryDayView({ meta, auction }: Props) {
  const days = meta.delivery_days;
  const [dateParam, setDate] = useSearchParam("date");
  const date = dateParam && days.includes(dateParam) ? dateParam : days[0];
  const query = useDeliveryDay(date, auction.id);
  const [showLater, setShowLater] = useState(false);
  if (!date) return <ErrorState error={new Error("No delivery days available")} />;
  const index = days.indexOf(date);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          aria-label="Previous day"
          disabled={index <= 0}
          onClick={() => setDate(days[index - 1] ?? date)}
          className="rounded-md bg-white px-3 py-1.5 text-sm shadow-sm ring-1 ring-slate-300 disabled:opacity-40"
        >
          ←
        </button>
        <label className="text-sm">
          <span className="sr-only">Delivery day</span>
          <select
            value={date}
            onChange={(event) => setDate(event.target.value)}
            className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm shadow-sm"
          >
            {days.map((day) => (
              <option key={day} value={day}>
                Delivery {formatDeliveryDay(day)}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          aria-label="Next day"
          disabled={index >= days.length - 1}
          onClick={() => setDate(days[index + 1] ?? date)}
          className="rounded-md bg-white px-3 py-1.5 text-sm shadow-sm ring-1 ring-slate-300 disabled:opacity-40"
        >
          →
        </button>
      </div>

      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState error={query.error} onRetry={() => void query.refetch()} />
      ) : (
        <DayContent data={query.data} showLater={showLater} onToggleLater={setShowLater} />
      )}
    </div>
  );
}

type ContentProps = {
  data: DeliveryDay;
  showLater: boolean;
  onToggleLater: (value: boolean) => void;
};

function DayContent({ data, showLater, onToggleLater }: ContentProps) {
  const { decision, summary } = data;
  const runs = decision.runs_used.map(formatUkTime).join(", ") || "none";
  return (
    <>
      <p className="text-sm text-slate-600">
        Delivery {formatUkDayTime(data.window_start)} → {formatUkDayTime(data.window_end)} ·{" "}
        {data.auction.label} gate closed {formatUkDayTime(decision.cutoff)} · forecast run used:{" "}
        {runs} (lead time {formatHours(decision.lead_hours_min)}–
        {formatHours(decision.lead_hours_max)})
      </p>

      {summary && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          <KpiCard
            label="Forecast energy"
            value={`${summary.forecast_gwh.toFixed(1)} GWh`}
            hint="at gate closure"
          />
          <KpiCard label="Actual energy" value={`${summary.actual_gwh.toFixed(1)} GWh`} />
          <KpiCard
            label="Day error"
            value={`${summary.error_gwh > 0 ? "+" : ""}${summary.error_gwh.toFixed(1)} GWh`}
            hint={`${summary.error_pct > 0 ? "+" : ""}${summary.error_pct.toFixed(0)}% of actual`}
            tone={Math.abs(summary.error_pct) > 10 ? "bad" : "neutral"}
          />
          <KpiCard label="Mean absolute error" value={formatMW(summary.mae_mw)} hint="per hour" />
          <KpiCard
            label="Largest miss"
            value={formatSignedGW(summary.largest_miss_mw)}
            hint={`at ${formatUkTime(summary.largest_miss_at)}`}
            tone="bad"
          />
        </div>
      )}

      <Card
        title="Wind: what you bought on vs what happened"
        subtitle="Forecast available at gate closure, calibrated P50 with P10–P90 band, and actual outturn"
        actions={
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={showLater}
              onChange={(event) => onToggleLater(event.target.checked)}
            />
            Show later runs ({data.later_runs.length})
          </label>
        }
      >
        <DeliveryDayChart data={data} showLater={showLater} />
      </Card>

      <Card title="Hourly detail">
        <HourlyTable data={data} />
      </Card>
    </>
  );
}
