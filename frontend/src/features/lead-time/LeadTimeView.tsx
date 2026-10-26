import { useDeferredValue, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Meta } from "../../api/client";
import { useLeadTime } from "../../api/hooks";
import { Card } from "../../components/Card";
import { KpiCard } from "../../components/KpiCard";
import { ErrorState, Loading } from "../../components/States";
import { GW_DOMAIN, gwTick, tooltipValue } from "../../lib/chart";
import { ACTUAL, FORECAST, GRID } from "../../lib/colors";
import {
  formatDayShort,
  formatDeliveryDay,
  formatGW,
  formatSignedGW,
  formatUkDayTime,
  toMs,
} from "../../lib/format";

export function LeadTimeView({ meta }: { meta: Meta }) {
  const days = meta.delivery_days;
  const [start, setStart] = useState(days[0] ?? "");
  const [end, setEnd] = useState(days[days.length - 1] ?? "");
  const [hours, setHours] = useState(4);
  const deferredHours = useDeferredValue(hours);
  const query = useLeadTime(start, end, deferredHours);

  const daySelect = (label: string, value: string, onChange: (day: string) => void) => (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-slate-500">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm shadow-sm"
      >
        {days.map((day) => (
          <option key={day} value={day}>
            {formatDeliveryDay(day)}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="space-y-4">
      <Card
        title="Lead-time explorer"
        subtitle="For each hour, the latest forecast published at least this long before it. Forecasts more than 48 h ahead are ignored."
      >
        <div className="flex flex-wrap items-center gap-4">
          {daySelect("From", start, (day) => {
            setStart(day);
            if (day > end) setEnd(day);
          })}
          {daySelect("To", end, (day) => {
            setEnd(day);
            if (day < start) setStart(day);
          })}
          <label className="flex flex-1 items-center gap-3 text-sm">
            <span className="text-slate-500">Lead time</span>
            <input
              type="range"
              min={0}
              max={48}
              step={1}
              value={hours}
              onChange={(event) => setHours(Number(event.target.value))}
              className="w-full max-w-xs accent-blue-600"
            />
            <span className="w-12 font-medium tabular-nums">{hours} h</span>
          </label>
        </div>
      </Card>

      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState error={query.error} onRetry={() => void query.refetch()} />
      ) : !query.data.summary ? (
        // WINDFOR runs extend about 47 h, so the longest lead times can have no data at all.
        <Card title="No data at this lead time">
          <p className="text-sm text-slate-600">
            No forecast run reaches {query.data.hours_ahead} h ahead in this window. WINDFOR runs
            cover roughly the next 47 hours; choose a shorter lead time.
          </p>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiCard label="MAE" value={formatGW(query.data.summary.mae_mw)} />
            <KpiCard label="RMSE" value={formatGW(query.data.summary.rmse_mw)} />
            <KpiCard label="Bias" value={formatSignedGW(query.data.summary.bias_mw)} />
            <KpiCard label="Hours compared" value={String(query.data.summary.n)} />
          </div>
          <Card title={`Actual vs forecast published at least ${query.data.hours_ahead} h ahead`}>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart
                data={query.data.points.map((p) => ({
                  t: toMs(p.start_time),
                  actual: p.actual_mw,
                  forecast: p.forecast_mw,
                }))}
                margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
              >
                <CartesianGrid stroke={GRID} vertical={false} />
                <XAxis
                  dataKey="t"
                  type="number"
                  scale="time"
                  domain={["dataMin", "dataMax"]}
                  tickFormatter={(v: number) => formatDayShort(v)}
                  minTickGap={40}
                />
                <YAxis domain={GW_DOMAIN} tickCount={6} tickFormatter={gwTick} width={40} />
                <Tooltip
                  labelFormatter={(v) => formatUkDayTime(Number(v))}
                  formatter={(value) => tooltipValue(value)}
                />
                <Legend />
                <Line
                  dataKey="actual"
                  name="Actual"
                  stroke={ACTUAL}
                  dot={false}
                  strokeWidth={1.5}
                  isAnimationActive={false}
                />
                <Line
                  dataKey="forecast"
                  name="Forecast"
                  stroke={FORECAST}
                  dot={false}
                  strokeWidth={1.5}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}
    </div>
  );
}
