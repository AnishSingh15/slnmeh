import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";

export function renderWithQuery(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

/** Stub fetch: responds with the fixture registered for the request path, else 404. */
export function mockFetch(routes: Record<string, unknown>) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const { pathname } = new URL(String(input), "http://localhost");
    const body = routes[pathname];
    return body === undefined
      ? new Response(JSON.stringify({ detail: "not found" }), { status: 404 })
      : new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
  });
}
