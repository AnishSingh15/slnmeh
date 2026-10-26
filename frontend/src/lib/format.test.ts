import {
  formatDeliveryDay,
  formatGW,
  formatMW,
  formatPct,
  formatSignedGW,
  formatUkTime,
} from "./format";

describe("format", () => {
  it("shows times in UK local time across clock changes", () => {
    expect(formatUkTime("2026-01-12T07:30:00Z")).toBe("07:30");
    expect(formatUkTime("2026-07-01T07:30:00Z")).toBe("08:30");
  });
  it("formats delivery days", () => {
    expect(formatDeliveryDay("2026-01-12")).toBe("Mon 12 Jan");
  });
  it("formats power", () => {
    expect(formatGW(1749)).toBe("1.75 GW");
    expect(formatGW(null)).toBe("–");
    expect(formatSignedGW(1749)).toBe("+1.75 GW");
    expect(formatSignedGW(-500)).toBe("−0.50 GW");
    expect(formatMW(12345.6)).toBe("12,346 MW");
    expect(formatPct(0.784)).toBe("78%");
  });
});
