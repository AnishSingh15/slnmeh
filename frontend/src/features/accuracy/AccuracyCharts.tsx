import {
  Bar,
  BarChart,
  Brush,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Accuracy, GroupStat } from "../../api/client";
import { GW_DOMAIN, gwAxis, gwTick, tooltipValue } from "../../lib/chart";
import { ACTUAL, BIAS, CALIBRATED, FORECAST, GRID, HIGHLIGHT } from "../../lib/colors";
import { formatDayShort, formatDeliveryDay, formatUkDayTime, toMs } from "../../lib/format";

const fmt = (value: unknown) => tooltipValue(value);

export function WindowChart({ series }: { series: Accuracy["series"] }) {
  const data = series.map((r) => ({
    t: toMs(r.start_time),
    actual: r.actual_mw,
    forecast: r.forecast_mw,
    p50: r.p50_mw,
  }));
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
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
        <Tooltip labelFormatter={(v) => formatUkDayTime(Number(v))} formatter={fmt} />
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
          name="Forecast at gate closure"
          stroke={FORECAST}
          dot={false}
          strokeWidth={1.5}
          isAnimationActive={false}
        />
        <Line
          dataKey="p50"
          name="Calibrated P50"
          stroke={CALIBRATED}
          dot={false}
          strokeWidth={1.5}
          strokeDasharray="5 3"
          isAnimationActive={false}
        />
        <Brush dataKey="t" height={24} tickFormatter={(v: number) => formatDayShort(v)} />
      </LineChart>
    </ResponsiveContainer>
  );
}

type LeadProps = { rows: GroupStat[]; min: number; max: number };

export function LeadTimeChart({ rows, min, max }: LeadProps) {
  const data = rows.map((g) => ({ lead: Number(g.key) + 0.5, mae: g.mae_mw, bias: g.bias_mw }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="lead"
          type="number"
          domain={[0, 48]}
          ticks={[0, 6, 12, 18, 24, 30, 36, 42, 48]}
          unit=" h"
        />
        <YAxis
          {...gwAxis(data.flatMap((d) => [d.mae, d.bias]))}
          tickFormatter={gwTick}
          width={40}
        />
        <Tooltip
          labelFormatter={(v) =>
            `Lead time ${Math.floor(Number(v))}–${Math.floor(Number(v)) + 1} h`
          }
          formatter={fmt}
        />
        <Legend />
        <ReferenceArea
          x1={min}
          x2={max}
          fill={HIGHLIGHT}
          fillOpacity={0.6}
          label={{ value: "Day-ahead decision", position: "insideTop", fontSize: 11 }}
        />
        <Bar dataKey="mae" name="MAE" fill={FORECAST} barSize={6} isAnimationActive={false} />
        <Line
          dataKey="bias"
          name="Bias (forecast − actual)"
          stroke={BIAS}
          dot={false}
          strokeWidth={2}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function HourChart({ rows }: { rows: GroupStat[] }) {
  const data = rows.map((g) => ({ hour: `${g.key.padStart(2, "0")}:00`, mae: g.mae_mw }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="hour" interval={2} />
        <YAxis {...gwAxis(data.map((d) => d.mae))} tickFormatter={gwTick} width={40} />
        <Tooltip formatter={fmt} />
        <Bar dataKey="mae" name="MAE" fill={FORECAST} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function LevelChart({ rows }: { rows: GroupStat[] }) {
  const data = rows.map((g) => ({ level: g.key, mae: g.mae_mw, bias: g.bias_mw, n: g.n }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="level" />
        <YAxis
          {...gwAxis(data.flatMap((d) => [d.mae, d.bias]))}
          tickFormatter={gwTick}
          width={40}
        />
        <Tooltip formatter={fmt} />
        <Legend />
        <Bar dataKey="mae" name="MAE" fill={FORECAST} isAnimationActive={false} />
        <Bar dataKey="bias" name="Bias" fill={BIAS} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

type DailyProps = { rows: GroupStat[]; onOpenDay: (date: string) => void };

export function DailyChart({ rows, onOpenDay }: DailyProps) {
  const worst = new Set(
    [...rows]
      .sort((a, b) => b.mae_mw - a.mae_mw)
      .slice(0, 3)
      .map((r) => r.key),
  );
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="key"
          tickFormatter={(k: string) => formatDayShort(`${k}T12:00:00Z`)}
          minTickGap={16}
        />
        <YAxis {...gwAxis(rows.map((r) => r.mae_mw))} tickFormatter={gwTick} width={40} />
        <Tooltip
          labelFormatter={(k) => `Delivery ${formatDeliveryDay(String(k))}`}
          formatter={fmt}
        />
        <Bar
          dataKey="mae_mw"
          name="Daily MAE"
          cursor="pointer"
          isAnimationActive={false}
          onClick={(_, index) => {
            const row = rows[index];
            if (row) onOpenDay(row.key);
          }}
        >
          {rows.map((r) => (
            <Cell key={r.key} fill={worst.has(r.key) ? BIAS : FORECAST} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
