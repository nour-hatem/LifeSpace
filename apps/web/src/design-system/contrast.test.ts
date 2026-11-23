import { describe, expect, it } from "vitest";

import { blend, contrastRatio, hexToRgb, relativeLuminance } from "./contrast";
import { chipText, colors } from "./tokens";

type TokenPair = {
  label: string;
  foreground: string;
  background: string;
  minimum: number;
};

const AA_TEXT = 4.5;
const AA_NON_TEXT = 3;

const tokenPairs: TokenPair[] = [
  { label: "text on background", foreground: colors.text, background: colors.bg, minimum: AA_TEXT },
  {
    label: "text on surface",
    foreground: colors.text,
    background: colors.surface,
    minimum: AA_TEXT,
  },
  {
    label: "muted text on background",
    foreground: colors.textMuted,
    background: colors.bg,
    minimum: AA_TEXT,
  },
  {
    label: "muted text on surface",
    foreground: colors.textMuted,
    background: colors.surface,
    minimum: AA_TEXT,
  },
  {
    label: "primary on background",
    foreground: colors.primary,
    background: colors.bg,
    minimum: AA_TEXT,
  },
  {
    label: "primary on surface",
    foreground: colors.primary,
    background: colors.surface,
    minimum: AA_TEXT,
  },
  {
    label: "cyan on background",
    foreground: colors.cyan,
    background: colors.bg,
    minimum: AA_TEXT,
  },
  {
    label: "cyan on surface",
    foreground: colors.cyan,
    background: colors.surface,
    minimum: AA_TEXT,
  },
  {
    label: "success on background",
    foreground: colors.success,
    background: colors.bg,
    minimum: AA_TEXT,
  },
  {
    label: "success on surface",
    foreground: colors.success,
    background: colors.surface,
    minimum: AA_TEXT,
  },
  {
    label: "warning on background",
    foreground: colors.warning,
    background: colors.bg,
    minimum: AA_TEXT,
  },
  {
    label: "warning on surface",
    foreground: colors.warning,
    background: colors.surface,
    minimum: AA_TEXT,
  },
  {
    label: "danger on background",
    foreground: colors.danger,
    background: colors.bg,
    minimum: AA_TEXT,
  },
  {
    label: "danger on surface",
    foreground: colors.danger,
    background: colors.surface,
    minimum: AA_TEXT,
  },
  {
    label: "secondary on background",
    foreground: colors.secondary,
    background: colors.bg,
    minimum: AA_TEXT,
  },
  {
    label: "text on filled primary",
    foreground: colors.text,
    background: colors.fillPrimary,
    minimum: AA_TEXT,
  },
  {
    label: "text on filled danger",
    foreground: colors.text,
    background: colors.fillDanger,
    minimum: AA_TEXT,
  },
  {
    label: "focus ring on background",
    foreground: colors.focus,
    background: colors.bg,
    minimum: AA_NON_TEXT,
  },
  {
    label: "focus ring on surface",
    foreground: colors.focus,
    background: colors.surface,
    minimum: AA_NON_TEXT,
  },
];

const chipTones = [
  { name: "neutral", tone: colors.textMuted, text: chipText.neutral },
  { name: "primary", tone: colors.primary, text: chipText.primary },
  { name: "success", tone: colors.success, text: chipText.success },
  { name: "warning", tone: colors.warning, text: chipText.warning },
  { name: "danger", tone: colors.danger, text: chipText.danger },
  { name: "violet", tone: colors.secondary, text: chipText.violet },
];

describe("contrast helpers", () => {
  it("parses six digit and three digit hex colors", () => {
    expect(hexToRgb("#080D1B")).toEqual({ r: 8, g: 13, b: 27 });
    expect(hexToRgb("#fff")).toEqual({ r: 255, g: 255, b: 255 });
  });

  it("rejects malformed hex colors", () => {
    expect(() => hexToRgb("not-a-color")).toThrow(/Invalid hex color/);
  });

  it("computes relative luminance at the extremes", () => {
    expect(relativeLuminance("#000000")).toBe(0);
    expect(relativeLuminance("#ffffff")).toBeCloseTo(1, 5);
  });

  it("puts black on white at 21 to 1", () => {
    expect(contrastRatio("#000000", "#ffffff")).toBeCloseTo(21, 5);
  });

  it("puts white on white at 1 to 1", () => {
    expect(contrastRatio("#ffffff", "#ffffff")).toBeCloseTo(1, 5);
  });

  it("puts #777777 on white at about 4.48 to 1", () => {
    expect(contrastRatio("#777777", "#ffffff")).toBeCloseTo(4.48, 1);
  });

  it("blends a foreground color over an opaque background", () => {
    expect(blend("#ffffff", "#000000", 0.5)).toBe("#808080");
    expect(blend(colors.primary, colors.surface, 0)).toBe(colors.surface.toLowerCase());
  });
});

describe("WCAG AA over the real tokens", () => {
  for (const pair of tokenPairs) {
    const ratio = contrastRatio(pair.foreground, pair.background);
    it(`${pair.label} is ${ratio.toFixed(2)} to 1 (minimum ${pair.minimum})`, () => {
      expect(ratio).toBeGreaterThanOrEqual(pair.minimum);
    });
  }

  for (const chip of chipTones) {
    const tinted = blend(chip.tone, colors.surface, 0.16);
    const ratio = contrastRatio(chip.text, tinted);
    it(`chip ${chip.name} text on ${tinted} is ${ratio.toFixed(2)} to 1 (minimum ${AA_TEXT})`, () => {
      expect(ratio).toBeGreaterThanOrEqual(AA_TEXT);
    });
  }

  it("violet is not used as text on the surface", () => {
    expect(contrastRatio(colors.secondary, colors.surface)).toBeLessThan(AA_TEXT);
  });
});
