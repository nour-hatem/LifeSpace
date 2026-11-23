/**
 * WCAG 2.x contrast helpers with no dependencies (ADR 0003 item 3).
 * Used by the automated contrast test over the real design tokens.
 */

/** An sRGB color with channels in the 0 to 255 range. */
export type Rgb = {
  r: number;
  g: number;
  b: number;
};

const HEX_PATTERN = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i;

function expandHex(hex: string): string {
  const value = hex.trim();
  if (!HEX_PATTERN.test(value)) {
    throw new Error(`Invalid hex color: ${hex}`);
  }
  const digits = value.startsWith("#") ? value.slice(1) : value;
  if (digits.length === 3) {
    const [r, g, b] = digits;
    return `#${r}${r}${g}${g}${b}${b}`;
  }
  return `#${digits}`;
}

/** Parses a #rgb or #rrggbb hex color into 0 to 255 channels (ADR 0003 item 3). */
export function hexToRgb(hex: string): Rgb {
  const value = expandHex(hex);
  return {
    r: Number.parseInt(value.slice(1, 3), 16),
    g: Number.parseInt(value.slice(3, 5), 16),
    b: Number.parseInt(value.slice(5, 7), 16),
  };
}

function toHexChannel(value: number): string {
  const clamped = Math.min(255, Math.max(0, Math.round(value)));
  return clamped.toString(16).padStart(2, "0");
}

/** Formats 0 to 255 channels as a lowercase hex color (ADR 0003 item 3). */
export function rgbToHex({ r, g, b }: Rgb): string {
  return `#${toHexChannel(r)}${toHexChannel(g)}${toHexChannel(b)}`;
}

function linearize(channel: number): number {
  const value = channel / 255;
  return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
}

/** Relative luminance of a hex color using the WCAG 2.x formula (ADR 0003 item 3). */
export function relativeLuminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex);
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b);
}

/** Contrast ratio between two hex colors, from 1 to 21 (ADR 0003 item 3). */
export function contrastRatio(foregroundHex: string, backgroundHex: string): number {
  const foreground = relativeLuminance(foregroundHex);
  const background = relativeLuminance(backgroundHex);
  const lighter = Math.max(foreground, background);
  const darker = Math.min(foreground, background);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Composites a foreground hex color at the given alpha over an opaque
 * background and returns the resulting hex color (ADR 0003 item 3).
 */
export function blend(foregroundHex: string, backgroundHex: string, alpha: number): string {
  const foreground = hexToRgb(foregroundHex);
  const background = hexToRgb(backgroundHex);
  return rgbToHex({
    r: foreground.r * alpha + background.r * (1 - alpha),
    g: foreground.g * alpha + background.g * (1 - alpha),
    b: foreground.b * alpha + background.b * (1 - alpha),
  });
}
