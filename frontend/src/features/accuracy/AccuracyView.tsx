import type { AuctionInfo } from "../../api/client";
import { useAccuracy } from "../../api/hooks";
import { Card } from "../../components/Card";
import { KpiCard } from "../../components/KpiCard";
import { ErrorState, Loading } from "../../components/States";
import { formatGW, formatPct, formatSignedGW } from "../../lib/format";
import { DailyChart, HourChart, LeadTimeChart, LevelChart, WindowChart } from "./AccuracyCharts";
import { headline } from "./headline";
import { MetricsTable } from "./MetricsTable";

type Props = { auction: AuctionInfo; onOpenDay: (date: string) => void };

export function AccuracyView({ auction, onOpenDay }: Props) {
  const query = useAccuracy(auction.id);
  if (query.isPending) return <Loading />;
  if (query.isError) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  const acc = query.data;
  const gain = 1 - acc.calibrated.mae_mw / acc.raw.mae_mw;
  const cal = acc.calibration;

  return (
    <div className="space-y-4">
      <p className="max-w-4xl text-sm leading-relaxed text-slate-700">{headline(acc)}</p>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiCard
          label="Forecast MAE"
          value={formatGW(acc.raw.mae_mw)}
          hint={`${formatPct(acc.raw.nmae)} of mean wind`}
        />
        <KpiCard
          label="Forecast bias"
          value={formatSignedGW(acc.raw.bias_mw)}
          hint="positive = too high"
          tone="bad"
        />
        <KpiCard
          label="Calibrated MAE"
          value={formatGW(acc.calibrated.mae_mw)}
          hint={`${formatPct(gain)} lower`}
          tone="good"
        />
        <KpiCard
          label="Band coverage"
          value={formatPct(acc.band_coverage)}
          hint="of hours inside P10–P90 (target 80%)"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
        <Card
          title="Accuracy metrics"
          subtitle={`${acc.auction.label}, gate closure ${acc.auction.gate_closure} on D−1`}
        >
          <MetricsTable acc={acc} />
        </Card>
        <Card title="How the calibration works">
          <div className="space-y-2 text-sm leading-relaxed text-slate-700">
            <p className="font-medium tabular-nums">
              actual ≈ {formatGW(cal.intercept_mw)} + {cal.slope.toFixed(2)} × forecast
            </p>
            <p>
              Across the pilot, each additional 1 GW of forecast wind brought only about{" "}
              {formatGW(cal.slope * 1000)} on average. The band adds the typical spread of misses:{" "}
              {formatSignedGW(cal.p10_offset_mw)} for the low case (P10) and{" "}
              {formatSignedGW(cal.p90_offset_mw)} for the high case (P90).
            </p>
            <p>
              Use P50 as the base case. When being short is expensive, P10 is the wind you can count
              on nine hours in ten.
            </p>
          </div>
        </Card>
      </div>

      <Card
        title="Actual vs forecast, whole pilot"
        subtitle="Drag the handles below the chart to zoom"
      >
        <WindowChart series={acc.series} />
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card
          title="Error grows with lead time"
          subtitle="All forecast runs, 1-hour lead-time bins; shaded = this auction's day-ahead lead times"
        >
          <LeadTimeChart
            rows={acc.by_lead_time}
            min={acc.decision_lead_hours_min}
            max={acc.decision_lead_hours_max}
          />
        </Card>
        <Card
          title="Over-forecast grows with wind level"
          subtitle="Forecast at gate closure, by forecast level"
        >
          <LevelChart rows={acc.by_level} />
        </Card>
        <Card title="Error by hour of day" subtitle="MAE by delivery hour (UK time)">
          <HourChart rows={acc.by_hour} />
        </Card>
        <Card
          title="Error by delivery day"
          subtitle="Click a bar to open that day; red = three worst days"
        >
          <DailyChart rows={acc.daily} onOpenDay={onOpenDay} />
        </Card>
      </div>
    </div>
  );
}
