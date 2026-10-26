import type { DeliveryDay } from "../../api/client";
import { downloadCsv, toCsv } from "../../lib/csv";
import { formatUkTime } from "../../lib/format";

const fmt = (mw: number | null) => (mw == null ? "–" : Math.round(mw).toLocaleString("en-GB"));
const signed = (mw: number | null) => (mw == null ? "–" : `${mw > 0 ? "+" : ""}${fmt(mw)}`);

export function HourlyTable({ data }: { data: DeliveryDay }) {
  const exportCsv = () => {
    const csv = toCsv(
      [
        "start_time_utc",
        "hour_uk",
        "forecast_mw",
        "p10_mw",
        "p50_mw",
        "p90_mw",
        "actual_mw",
        "error_mw",
      ],
      data.hours.map((h) => [
        h.start_time,
        formatUkTime(h.start_time),
        h.forecast_mw,
        h.p10_mw,
        h.p50_mw,
        h.p90_mw,
        h.actual_mw,
        h.error_mw,
      ]),
    );
    downloadCsv(`winddesk_${data.delivery_day}_${data.auction.id}.csv`, csv);
  };

  return (
    <div>
      <div className="mb-2 flex justify-end">
        <button
          type="button"
          onClick={exportCsv}
          className="rounded-md bg-white px-3 py-1.5 text-sm font-medium shadow-sm ring-1 ring-slate-300 hover:bg-slate-50"
        >
          Export CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-right text-sm tabular-nums">
          <thead className="text-xs text-slate-500">
            <tr>
              <th className="py-1.5 text-left font-medium">Hour (UK)</th>
              <th className="py-1.5 font-medium">Forecast</th>
              <th className="py-1.5 font-medium">P10</th>
              <th className="py-1.5 font-medium">P50</th>
              <th className="py-1.5 font-medium">P90</th>
              <th className="py-1.5 font-medium">Actual</th>
              <th className="py-1.5 font-medium">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.hours.map((h) => (
              <tr key={h.start_time}>
                <td className="py-1.5 text-left">{formatUkTime(h.start_time)}</td>
                <td className="py-1.5">{fmt(h.forecast_mw)}</td>
                <td className="py-1.5 text-slate-500">{fmt(h.p10_mw)}</td>
                <td className="py-1.5">{fmt(h.p50_mw)}</td>
                <td className="py-1.5 text-slate-500">{fmt(h.p90_mw)}</td>
                <td className="py-1.5">{fmt(h.actual_mw)}</td>
                <td
                  className={`py-1.5 ${(h.error_mw ?? 0) > 0 ? "text-rose-700" : "text-emerald-700"}`}
                >
                  {signed(h.error_mw)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        MW, hourly. Error = forecast − actual: positive means the forecast was too high.
      </p>
    </div>
  );
}
