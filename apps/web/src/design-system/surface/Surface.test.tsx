import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Surface } from "./Surface";

describe("Surface", () => {
  it("applies the floating class when elevation is floating", () => {
    render(<Surface elevation="floating">Panel content</Surface>);

    const surface = screen.getByText("Panel content");
    expect(surface.className).toContain("surface");
    expect(surface.className).toContain("floating");
  });

  it("is flat by default", () => {
    render(<Surface>Panel content</Surface>);

    const surface = screen.getByText("Panel content");
    expect(surface.className).toContain("flat");
    expect(surface.className).not.toContain("floating");
  });
});
