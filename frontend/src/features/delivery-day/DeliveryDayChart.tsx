import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DeliveryDay } from "../../api/client";
import { GW_DOMAIN, gwTick, hourTicks, tooltipValue } from "../../lib/chart";
import { ACTUAL, BAND, CALIBRATED, FORECAST, GRID, LATER } from "../../lib/colors";
import { formatUkDayTime, formatUkTime, toMs } from "../../lib/format";

export type ChartRow = {
  t: number;
  actual?: number;
  forecast?: number;
  p50?: number;
  band?: [number, number];
  [run: `run${number}`]: number | undefined;
};

/** One row per timestamp: half-hourly actuals plus hourly forecast, band and later runs. */
export function buildRows(data: DeliveryDay, showLater: boolean): ChartRow[] {
  const rows = new Map<number, ChartRow>();
  const at = (iso: string): ChartRow => {
    const t = toMs(iso);
    let row = rows.get(t);
    if (!row) {
      row = { t };
      rows.set(t, row);
    }
    return row;
  };
  for (const point of data.actuals_half_hourly) at(point.start_time).actual = point.mw;
  for (const hour of data.hours) {
    const row = at(hour.start_time);
    if (hour.forecast_mw != null) row.forecast = hour.forecast_mw;
    if (hour.p50_mw != null) row.p50 = hour.p50_mw;
    if (hour.p10_mw != null && hour.p90_mw != null) row.band = [hour.p10_mw, hour.p90_mw];
  }
  if (showLater) {
    data.later_runs.forEach((run, i) => {
      for (const point of run.points) at(point.start_time)[`run${i}`] = point.mw;
    });
  }
  return [...rows.values()].sort((a, b) => a.t - b.t);
}

export function DeliveryDayChart({ data, showLater }: { data: DeliveryDay; showLater: boolean }) {
  const rows = buildRows(data, showLater);
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="t"
          type="number"
          scale="time"
          domain={[toMs(data.window_start), toMs(data.window_end)]}
          ticks={hourTicks(data.window_start, data.window_end, 3)}
          tickFormatter={(v: number) => formatUkTime(v)}
        />
        <YAxis
          domain={GW_DOMAIN}
          tickCount={6}
          tickFormatter={gwTick}
          width={44}
          label={{ value: "GW", angle: -90, position: "insideLeft" }}
        />
        <Tooltip
          labelFormatter={(v) => formatUkDayTime(Number(v))}
          formatter={(value) => tooltipValue(value)}
        />
        <Legend />
        <Area
          dataKey="band"
          name="P10–P90 band"
          stroke="none"
          fill={BAND}
          fillOpacity={0.6}
          connectNulls
          isAnimationActive={false}
        />
        {showLater &&
          data.later_runs.map((run, i) => (
            <Line
              key={run.publish_time}
              dataKey={`run${i}`}
              name={`Later run ${formatUkTime(run.publish_time)}`}
              stroke={LATER}
              strokeWidth={1}
              strokeDasharray="2 3"
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          ))}
        <Line
          dataKey="actual"
          name="Actual"
          stroke={ACTUAL}
          strokeWidth={2}
          dot={false}
          connectNulls
          isAnimationActive={false}
        />
        <Line
          dataKey="forecast"
          name="Forecast at gate closure"
          stroke={FORECAST}
          strokeWidth={2}
          dot={false}
          connectNulls
          isAnimationActive={false}
        />
        <Line
          dataKey="p50"
          name="Calibrated P50"
          stroke={CALIBRATED}
          strokeWidth={2}
          strokeDasharray="6 4"
          dot={false}
          connectNulls
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
