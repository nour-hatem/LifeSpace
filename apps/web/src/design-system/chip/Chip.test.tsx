import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Chip } from "./Chip";

describe("Chip", () => {
  it("renders its text and tone class", () => {
    render(<Chip tone="danger">Overdue</Chip>);

    const chip = screen.getByText("Overdue");
    expect(chip.className).toContain("chip");
    expect(chip.className).toContain("danger");
  });

  it("renders an icon hidden from assistive technology", () => {
    const { container } = render(
      <Chip tone="primary" icon={<span>→</span>}>
        In progress
      </Chip>,
    );

    expect(screen.getByText("In progress")).toBeInTheDocument();
    const icon = container.querySelector('[aria-hidden="true"]');
    expect(icon).not.toBeNull();
    expect(icon).toHaveTextContent("→");
  });
});
