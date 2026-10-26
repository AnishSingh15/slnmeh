import { act, renderHook } from "@testing-library/react";
import { setSearchParams, useSearchParam } from "./url-state";

describe("useSearchParam", () => {
  beforeEach(() => window.history.replaceState(null, "", "/"));

  it("reads, writes and clears a query parameter", () => {
    const { result } = renderHook(() => useSearchParam("tab"));
    expect(result.current[0]).toBeNull();
    act(() => result.current[1]("accuracy"));
    expect(result.current[0]).toBe("accuracy");
    expect(window.location.search).toBe("?tab=accuracy");
    act(() => result.current[1](null));
    expect(result.current[0]).toBeNull();
  });

  it("updates several parameters in one history entry", () => {
    const { result } = renderHook(() => useSearchParam("date"));
    const before = window.history.length;
    act(() => setSearchParams({ tab: "day", date: "2026-01-12" }));
    expect(result.current[0]).toBe("2026-01-12");
    expect(window.history.length).toBe(before + 1);
  });
});
