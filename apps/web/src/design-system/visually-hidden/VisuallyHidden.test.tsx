import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { VisuallyHidden } from "./VisuallyHidden";

describe("VisuallyHidden", () => {
  it("renders its text for assistive technology", () => {
    render(<VisuallyHidden>Task completed</VisuallyHidden>);

    expect(screen.getByText("Task completed")).toBeInTheDocument();
  });
});
