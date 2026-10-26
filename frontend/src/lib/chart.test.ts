import { gwAxis, gwTick } from "./chart";

describe("chart helpers", () => {
  it("labels ticks in GW without rounding away decimals", () => {
    expect(gwTick(15000)).toBe("15");
    expect(gwTick(2500)).toBe("2.5");
  });

  it("chooses round GW steps that cover the data", () => {
    expect(gwAxis([1400, 2380])).toEqual({
      domain: [0, 2500],
      ticks: [0, 500, 1000, 1500, 2000, 2500],
    });
    expect(gwAxis([4600, 1200])).toEqual({
      domain: [0, 5000],
      ticks: [0, 1000, 2000, 3000, 4000, 5000],
    });
    expect(gwAxis([-600, 1700]).domain).toEqual([-1000, 2000]);
  });
});
