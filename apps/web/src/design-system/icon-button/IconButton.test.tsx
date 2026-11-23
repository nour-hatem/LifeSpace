import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IconButton } from "./IconButton";

describe("IconButton", () => {
  it("exposes its label as the accessible name", () => {
    render(<IconButton label="Close panel">×</IconButton>);

    expect(screen.getByRole("button", { name: "Close panel" })).toBeInTheDocument();
  });

  it("hides the icon from assistive technology", () => {
    const { container } = render(<IconButton label="Add task">+</IconButton>);

    const icon = container.querySelector('[aria-hidden="true"]');
    expect(icon).not.toBeNull();
    expect(icon).toHaveTextContent("+");
  });

  it("defaults to type button", () => {
    render(<IconButton label="Add task">+</IconButton>);

    expect(screen.getByRole("button", { name: "Add task" })).toHaveAttribute("type", "button");
  });
});
