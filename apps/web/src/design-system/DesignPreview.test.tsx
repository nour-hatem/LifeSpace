import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import { DesignPreview } from "./DesignPreview";

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );
}

describe("DesignPreview", () => {
  afterEach(() => {
    window.location.hash = "";
    vi.unstubAllGlobals();
  });

  it("renders every token section and primitive", () => {
    render(<DesignPreview />);

    expect(screen.getByRole("heading", { name: "Design preview" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Colors" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Buttons" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Surfaces" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Chips" })).toBeInTheDocument();
    expect(screen.getByText("اكتب تقرير المشروع")).toBeInTheDocument();
  });

  it("renders when the hash is #design-preview", () => {
    window.location.hash = "#design-preview";

    renderApp();

    expect(screen.getByRole("heading", { name: "Design preview" })).toBeInTheDocument();
  });

  it("shows the normal content otherwise", () => {
    window.location.hash = "";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      ),
    );

    renderApp();

    expect(screen.getByRole("heading", { name: "LifeSpace" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Design preview" })).not.toBeInTheDocument();
  });
});
