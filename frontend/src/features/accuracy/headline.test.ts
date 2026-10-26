import { accuracy } from "../../test/fixtures";
import { headline } from "./headline";

describe("headline", () => {
  it("summarises error, bias, calibration gain and band coverage", () => {
    expect(headline(accuracy)).toBe(
      "At gate closure the forecast missed actual wind by 2.04 GW per hour on average and was too high in 85% of hours, by 1.75 GW on average. Calibrated on the other pilot days, the average miss falls to 1.21 GW (41% lower), and the P10–P90 band contained 78% of hours (target 80%).",
    );
  });

  it("describes under-forecasting", () => {
    const under = {
      ...accuracy,
      raw: { ...accuracy.raw, bias_mw: -500, share_over_forecast: 0.3 },
    };
    expect(headline(under)).toContain("too low in 70% of hours, by 0.50 GW on average");
  });
});
