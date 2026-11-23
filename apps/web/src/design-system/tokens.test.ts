import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { hexToRgb } from "./contrast";
import {
  breakpoints,
  categoryAccents,
  chipText,
  colors,
  floatingSurface,
  fontSizes,
  fontWeights,
  lineHeights,
  motion,
  radii,
  spacing,
  zIndex,
} from "./tokens";

const FONT_SANS =
  'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Noto Sans Arabic", sans-serif';

// Vitest 5 replaces CSS imports (including the ?raw suffix) with an empty
// string while CSS processing is disabled, so the file is read directly. The
// module URL is held in a variable to keep Vite's asset rewriting away.
const moduleUrl = import.meta.url;
const tokensCss = readFileSync(new URL("./tokens.css", moduleUrl), "utf8");

const TYPE_SCALE_NAMES = ["xs", "sm", "md", "lg", "xl", "2xl", "3xl"] as const;

function normalize(value: string): string {
  return value
    .replace(/\s+/g, " ")
    .replace(/\s*,\s*/g, ", ")
    .trim();
}

function kebabCase(value: string): string {
  return value.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
}

function parseCustomProperties(css: string): Map<string, string> {
  const properties = new Map<string, string>();
  const pattern = /--([a-z0-9-]+)\s*:\s*([^;]+);/g;
  for (const match of css.matchAll(pattern)) {
    const name = match[1];
    const value = match[2];
    if (name && value) {
      properties.set(name, normalize(value));
    }
  }
  return properties;
}

function buildExpectedTokens(): Record<string, string> {
  const expected: Record<string, string> = {};

  for (const [name, value] of Object.entries(colors)) {
    expected[`color-${kebabCase(name)}`] = value.toLowerCase();
  }
  for (const [name, value] of Object.entries(chipText)) {
    expected[`color-${name}-text`] = value.toLowerCase();
  }
  for (const [name, value] of Object.entries(categoryAccents)) {
    expected[`accent-${name}`] = value.toLowerCase();
  }
  for (const [index, value] of spacing.entries()) {
    expected[`space-${index + 1}`] = `${value}px`;
  }
  expected["radius-control"] = `${radii.control}px`;
  expected["radius-panel"] = `${radii.panel}px`;
  expected["radius-round"] = `${radii.round}px`;
  expected["font-sans"] = FONT_SANS;
  for (const [index, value] of fontSizes.entries()) {
    const name = TYPE_SCALE_NAMES[index];
    if (!name) {
      throw new Error(`Unexpected font size index: ${index}`);
    }
    expected[`text-${name}`] = `${value}px`;
  }
  expected["leading-body"] = String(lineHeights.body);
  expected["leading-heading"] = String(lineHeights.heading);
  expected["weight-regular"] = String(fontWeights.regular);
  expected["weight-medium"] = String(fontWeights.medium);
  expected["weight-semibold"] = String(fontWeights.semibold);
  expected["shadow-floating"] = normalize(floatingSurface.shadow);
  expected["blur-surface"] = `${floatingSurface.blur}px`;

  const surface = hexToRgb(colors.surface);
  expected["surface-floating"] =
    `rgba(${surface.r}, ${surface.g}, ${surface.b}, ${floatingSurface.opacity})`;

  expected["duration-fast"] = `${motion.fast}ms`;
  expected["duration-panel"] = `${motion.panel}ms`;
  expected["duration-settle"] = `${motion.settle}ms`;
  expected["ease-out"] = motion.easeOut;

  expected["z-base"] = String(zIndex.base);
  expected["z-dock"] = String(zIndex.dock);
  expected["z-panel"] = String(zIndex.panel);
  expected["z-menu"] = String(zIndex.menu);
  expected["z-toast"] = String(zIndex.toast);

  return expected;
}

const expectedTokens = buildExpectedTokens();
const cssTokens = parseCustomProperties(tokensCss);

describe("design tokens", () => {
  it("parses custom properties from tokens.css", () => {
    expect(cssTokens.size).toBeGreaterThan(0);
  });

  for (const [name, value] of Object.entries(expectedTokens)) {
    it(`defines --${name} as ${value}`, () => {
      expect(cssTokens.get(name)).toBe(normalize(value));
    });
  }

  it("has no required token missing from tokens.css", () => {
    const missing = Object.keys(expectedTokens).filter((name) => !cssTokens.has(name));
    expect(missing).toEqual([]);
  });

  it("keeps breakpoints in tokens.ts because media queries cannot use variables", () => {
    expect(breakpoints).toEqual({ compact: 640, full: 1024, wide: 1440 });
    expect([...cssTokens.keys()].filter((name) => name.startsWith("breakpoint"))).toEqual([]);
  });
});
