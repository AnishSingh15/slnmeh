import { fireEvent, screen } from "@testing-library/react";
import App from "./App";
import { meta } from "./test/fixtures";
import { mockFetch, renderWithQuery } from "./test/render";

describe("App", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/?tab=method");
    mockFetch({ "/api/meta": meta });
  });
  afterEach(() => vi.restoreAllMocks());

  it("renders the shell and the method view", async () => {
    renderWithQuery(<App />);
    // The header renders while loading too, so wait for content that needs the data.
    expect(await screen.findByText("When the decision is made")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "WindDesk" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Method & data" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("keeps the selected auction in the URL", async () => {
    renderWithQuery(<App />);
    fireEvent.change(await screen.findByRole("combobox"), { target: { value: "n2ex_60" } });
    expect(window.location.search).toContain("auction=n2ex_60");
  });
});
