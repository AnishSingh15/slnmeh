import { formatGW } from "./format";

/** Y-axis tick: MW shown in GW (the axis is labelled); keeps a decimal rather than rounding. */
export const gwTick = (mw: number): string => {
  const gw = mw / 1000;
  return Number.isInteger(gw) ? String(gw) : gw.toFixed(1);
};

/** Y domain from 0 up to the next multiple of 5 GW; with tickCount 6 this gives whole-GW ticks. */
export const GW_DOMAIN: [number, (dataMax: number) => number] = [
  0,
  (dataMax) => Math.max(5000, Math.ceil(dataMax / 5000) * 5000),
];

/** Tooltip text for a single value or a [low, high] range. */
export function tooltipValue(value: unknown): string {
  if (Array.isArray(value)) return `${formatGW(Number(value[0]))} – ${formatGW(Number(value[1]))}`;
  return value == null ? "–" : formatGW(Number(value));
}

/** Tick positions (ms) every `stepHours` from start to end inclusive. */
export function hourTicks(startIso: string, endIso: string, stepHours: number): number[] {
  const ticks: number[] = [];
  for (let t = Date.parse(startIso); t <= Date.parse(endIso); t += stepHours * 3_600_000) {
    ticks.push(t);
  }
  return ticks;
}
