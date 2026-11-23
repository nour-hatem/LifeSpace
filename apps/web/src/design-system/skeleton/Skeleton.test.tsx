import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Skeleton } from "./Skeleton";

describe("Skeleton", () => {
  it("is decorative and applies its dimensions", () => {
    const { container } = render(<Skeleton width={120} height={20} />);

    const skeleton = container.firstElementChild;
    expect(skeleton).toHaveAttribute("aria-hidden", "true");
    expect(skeleton).toHaveStyle({ width: "120px", height: "20px" });
  });
});
