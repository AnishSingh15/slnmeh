import type { Accuracy, ErrorSummary } from "../../api/client";
import { formatGW, formatPct, formatSignedGW } from "../../lib/format";

const ROWS: { label: string; hint: string; value: (s: ErrorSummary) => string }[] = [
  {
    label: "Mean absolute error",
    hint: "Average size of the miss",
    value: (s) => formatGW(s.mae_mw),
  },
  {
    label: "Root mean square error",
    hint: "Weights big misses more",
    value: (s) => formatGW(s.rmse_mw),
  },
  { label: "Bias", hint: "Positive = forecast too high", value: (s) => formatSignedGW(s.bias_mw) },
  { label: "Normalised MAE", hint: "MAE ÷ mean actual wind", value: (s) => formatPct(s.nmae, 1) },
  {
    label: "P90 absolute error",
    hint: "9 hours in 10 missed by less than this",
    value: (s) => formatGW(s.p90_abs_error_mw),
  },
  {
    label: "Hours over-forecast",
    hint: "Wind came in below forecast",
    value: (s) => formatPct(s.share_over_forecast),
  },
];

export function MetricsTable({ acc }: { acc: Accuracy }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-sm">
        <thead className="text-left text-xs text-slate-500">
          <tr>
            <th className="py-1.5 font-medium">Metric ({acc.raw.n} delivery hours)</th>
            <th className="py-1.5 text-right font-medium">Forecast at gate closure</th>
            <th className="py-1.5 text-right font-medium">Calibrated P50</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {ROWS.map((row) => (
            <tr key={row.label}>
              <td className="py-2">
                <div className="font-medium text-slate-800">{row.label}</div>
                <div className="text-xs text-slate-500">{row.hint}</div>
              </td>
              <td className="py-2 text-right tabular-nums">{row.value(acc.raw)}</td>
              <td className="py-2 text-right tabular-nums text-emerald-700">
                {row.value(acc.calibrated)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-slate-500">
        Calibrated values for each day are fitted on the other days only (leave-one-day-out).
      </p>
    </div>
  );
}
