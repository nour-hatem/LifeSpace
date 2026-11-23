/**
 * Typed design tokens for LifeSpace.
 *
 * Every value mirrors docs/engineering/adr/0003-m3-frontend-decisions.md and
 * src/design-system/tokens.css; tokens.test.ts keeps both files in sync.
 * ADR 0003 items 2 to 7 define the palette, contrast, typography, spacing,
 * surfaces, and motion; item 8 defines the category accents.
 */

/** Palette and derived colors (ADR 0003 item 2). */
export const colors = {
  bg: "#080D1B",
  surface: "#111A2E",
  primary: "#3B82F6",
  secondary: "#8B5CF6",
  cyan: "#22D3EE",
  success: "#22C55E",
  warning: "#F59E0B",
  danger: "#EF4444",
  text: "#F8FAFC",
  textMuted: "#94A3B8",
  fillPrimary: "#2563EB",
  fillDanger: "#DC2626",
  focus: "#22D3EE",
} as const;

/**
 * Chip text colors (ADR 0003 items 3 and 8).
 *
 * A chip is its tone color at 16 percent over the surface. Primary, danger,
 * and violet do not reach 4.5:1 there, so their text tokens are lightened in
 * HSL just enough to pass (recorded ratios against the tinted chip background:
 * primary 4.52, danger 4.51, violet 4.52). Neutral, success, and warning
 * already pass and reuse the tone color (5.16, 5.79, and 6.16).
 */
export const chipText = {
  neutral: "#94A3B8",
  primary: "#5291F7",
  success: "#22C55E",
  warning: "#F59E0B",
  danger: "#F15B5B",
  violet: "#9F79F8",
} as const;

/** Category accent colors (ADR 0003 item 8). */
export const categoryAccents = {
  work: "#3B82F6",
  education: "#22D3EE",
  learning: "#8B5CF6",
  personal: "#94A3B8",
  projects: "#93C5FD",
} as const;

/** 4 px spacing grid in order (ADR 0003 item 5). */
export const spacing = [4, 8, 12, 16, 24, 32, 48, 64] as const;

/** Corner radii in pixels (ADR 0003 item 5). */
export const radii = {
  control: 6,
  panel: 12,
  round: 9999,
} as const;

/** Type scale in pixels (ADR 0003 item 4). */
export const fontSizes = [12, 14, 16, 18, 22, 28, 36] as const;

/** Font weights (ADR 0003 item 4). */
export const fontWeights = {
  regular: 400,
  medium: 500,
  semibold: 600,
} as const;

/** Line heights (ADR 0003 item 4). */
export const lineHeights = {
  body: 1.5,
  heading: 1.25,
} as const;

/**
 * Breakpoints in pixels (ADR 0003 item 13).
 *
 * CSS cannot use custom properties in media queries, so these live only here.
 */
export const breakpoints = {
  compact: 640,
  full: 1024,
  wide: 1440,
} as const;

/** Motion durations in milliseconds and the easing (ADR 0003 item 7). */
export const motion = {
  fast: 150,
  panel: 250,
  settle: 400,
  easeOut: "ease-out",
} as const;

/** Floating surface treatment (ADR 0003 item 6). */
export const floatingSurface = {
  opacity: 0.8,
  blur: 12,
  shadow: "0 8px 24px rgba(0,0,0,0.35)",
} as const;

/** Stacking order (ADR 0003 items 6 and 11). */
export const zIndex = {
  base: 0,
  dock: 20,
  panel: 30,
  menu: 40,
  toast: 50,
} as const;
