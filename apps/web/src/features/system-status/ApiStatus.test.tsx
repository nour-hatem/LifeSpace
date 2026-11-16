import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiStatus } from "./ApiStatus";

function renderApiStatus() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ApiStatus />
    </QueryClientProvider>,
  );
}

describe("ApiStatus", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows checking first and then ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      ),
    );

    renderApiStatus();

    expect(screen.getByText("API status: checking")).toBeInTheDocument();
    expect(await screen.findByText("API status: ok")).toBeInTheDocument();
  });

  it("shows unreachable when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    renderApiStatus();

    expect(await screen.findByText("API status: unreachable")).toBeInTheDocument();
  });
});
