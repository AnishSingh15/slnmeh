import { screen } from "@testing-library/react";
import { accuracy, epex } from "../../test/fixtures";
import { mockFetch, renderWithQuery } from "../../test/render";
import { AccuracyView } from "./AccuracyView";

describe("AccuracyView", () => {
  beforeEach(() => mockFetch({ "/api/accuracy": accuracy }));
  afterEach(() => vi.restoreAllMocks());

  it("shows the headline and raw vs calibrated metrics", async () => {
    renderWithQuery(<AccuracyView auction={epex} onOpenDay={() => {}} />);
    expect(await screen.findByText(/At gate closure the forecast missed/)).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Calibrated P50" })).toBeInTheDocument();
    expect(screen.getAllByText("+1.75 GW")).toHaveLength(2); // KPI card + metrics table
    expect(screen.getByText(/actual ≈ 0.75 GW \+ 0.81 × forecast/)).toBeInTheDocument();
  });
});
