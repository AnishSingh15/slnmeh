import type { Accuracy } from "../../api/client";
import { formatGW, formatPct } from "../../lib/format";

/** One-paragraph plain-English summary of the accuracy results. */
export function headline(acc: Accuracy): string {
  const { raw, calibrated } = acc;
  const over = raw.bias_mw >= 0;
  const share = over ? raw.share_over_forecast : 1 - raw.share_over_forecast;
  const gain = Math.round((1 - calibrated.mae_mw / raw.mae_mw) * 100);
  return (
    `At gate closure the forecast missed actual wind by ${formatGW(raw.mae_mw)} per hour on average ` +
    `and was too ${over ? "high" : "low"} in ${formatPct(share)} of hours, ` +
    `by ${formatGW(Math.abs(raw.bias_mw))} on average. ` +
    `Calibrated on the other pilot days, the average miss falls to ${formatGW(calibrated.mae_mw)} ` +
    `(${gain}% lower), and the P10–P90 band contained ${formatPct(acc.band_coverage)} of hours ` +
    `(target 80%).`
  );
}
