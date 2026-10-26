import { fireEvent, render, screen } from "@testing-library/react";
import * as csv from "../../lib/csv";
import { deliveryDay } from "../../test/fixtures";
import { HourlyTable } from "./HourlyTable";

describe("HourlyTable", () => {
  afterEach(() => vi.restoreAllMocks());

  it("lists each hour in UK time and exports CSV", () => {
    const download = vi.spyOn(csv, "downloadCsv").mockImplementation(() => {});
    render(<HourlyTable data={deliveryDay} />);
    expect(screen.getByText("23:00")).toBeInTheDocument();
    expect(screen.getByText("+2,000")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Export CSV" }));
    expect(download).toHaveBeenCalledOnce();
    const [filename, content] = download.mock.calls[0]!;
    expect(filename).toBe("winddesk_2026-01-02_epex_60.csv");
    expect(content.split("\n")[0]).toBe(
      "start_time_utc,hour_uk,forecast_mw,p10_mw,p50_mw,p90_mw,actual_mw,error_mw",
    );
  });
});
