import { deliveryDay } from "../../test/fixtures";
import { buildRows } from "./DeliveryDayChart";

describe("buildRows", () => {
  it("merges half-hourly actuals with hourly forecast and band", () => {
    const rows = buildRows(deliveryDay, false);
    expect(rows.map((r) => r.t)).toEqual([
      Date.parse("2026-01-01T23:00:00Z"),
      Date.parse("2026-01-01T23:30:00Z"),
      Date.parse("2026-01-02T00:00:00Z"),
      Date.parse("2026-01-02T00:30:00Z"),
    ]);
    expect(rows[0]).toMatchObject({
      actual: 9900,
      forecast: 12000,
      p50: 10500,
      band: [8000, 12500],
    });
    expect(rows[1]).toEqual({ t: Date.parse("2026-01-01T23:30:00Z"), actual: 10100 });
    expect(rows[0]?.run0).toBeUndefined();
  });

  it("adds later runs only when asked", () => {
    expect(buildRows(deliveryDay, true)[0]?.run0).toBe(11000);
  });
});
