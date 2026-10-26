import { fireEvent, screen } from "@testing-library/react";
import { leadTime, meta } from "../../test/fixtures";
import { mockFetch, renderWithQuery } from "../../test/render";
import { LeadTimeView } from "./LeadTimeView";

describe("LeadTimeView", () => {
  afterEach(() => vi.restoreAllMocks());

  it("requests the chosen lead time and shows its metrics", async () => {
    const fetchSpy = mockFetch({ "/api/lead-time": leadTime });
    renderWithQuery(<LeadTimeView meta={meta} />);
    expect(await screen.findAllByText("1.00 GW")).toHaveLength(2); // MAE + RMSE
    fireEvent.change(screen.getByRole("slider"), { target: { value: "24" } });
    expect(screen.getByText("24 h")).toBeInTheDocument();
    await vi.waitFor(() =>
      expect(fetchSpy.mock.calls.some(([url]) => String(url).includes("hours=24"))).toBe(true),
    );
  });
});
