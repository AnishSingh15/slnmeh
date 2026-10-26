const UK = "Europe/London";

const timeFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: UK,
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});
const dayFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: UK,
  weekday: "short",
  day: "numeric",
  month: "short",
});
const shortDayFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: UK,
  day: "numeric",
  month: "short",
});

export const toMs = (iso: string): number => new Date(iso).getTime();

/** "07:30" in UK local time. */
export const formatUkTime = (value: string | number): string => timeFmt.format(new Date(value));

/** "Sun 11 Jan 09:20" in UK local time. */
export const formatUkDayTime = (value: string | number): string =>
  `${dayFmt.format(new Date(value))} ${formatUkTime(value)}`;

/** "12 Jan" in UK local time. */
export const formatDayShort = (value: string | number): string =>
  shortDayFmt.format(new Date(value));

/** A delivery-day date (YYYY-MM-DD) as "Mon 12 Jan". */
export const formatDeliveryDay = (isoDate: string): string =>
  dayFmt.format(new Date(`${isoDate}T12:00:00Z`));

export const formatGW = (mw: number | null | undefined, digits = 2): string =>
  mw == null ? "–" : `${(mw / 1000).toFixed(digits)} GW`;

export const formatSignedGW = (mw: number, digits = 2): string => {
  const sign = mw > 0 ? "+" : mw < 0 ? "−" : "";
  return `${sign}${Math.abs(mw / 1000).toFixed(digits)} GW`;
};

export const formatMW = (mw: number | null | undefined): string =>
  mw == null ? "–" : `${Math.round(mw).toLocaleString("en-GB")} MW`;

export const formatPct = (ratio: number, digits = 0): string => `${(ratio * 100).toFixed(digits)}%`;

export const formatHours = (hours: number | null | undefined): string =>
  hours == null ? "–" : `${Number.isInteger(hours) ? hours : hours.toFixed(1)} h`;
