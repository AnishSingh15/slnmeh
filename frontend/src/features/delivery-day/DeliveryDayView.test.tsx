import { screen } from "@testing-library/react";
import { deliveryDay, epex, meta } from "../../test/fixtures";
import { mockFetch, renderWithQuery } from "../../test/render";
import { DeliveryDayView } from "./DeliveryDayView";

describe("DeliveryDayView", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/");
    mockFetch({ "/api/delivery-day": deliveryDay });
  });
  afterEach(() => vi.restoreAllMocks());

  it("shows the decision context and day KPIs", async () => {
    renderWithQuery(<DeliveryDayView meta={meta} auction={epex} />);
    expect(await screen.findByText(/forecast run used: 07:30/)).toBeInTheDocument();
    expect(screen.getByText("+2.5 GWh")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous day" })).toBeDisabled();
  });
});
