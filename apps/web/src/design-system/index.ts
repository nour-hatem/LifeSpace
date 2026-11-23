/**
 * Public surface of the LifeSpace design system (ADR 0003 items 2 to 8 and 14).
 * Import tokens, primitives, and contrast helpers from here.
 */

export * from "./tokens";
export * from "./contrast";

export { Button } from "./button/Button";
export type { ButtonProps, ButtonSize, ButtonVariant } from "./button/Button";

export { IconButton } from "./icon-button/IconButton";
export type { IconButtonProps } from "./icon-button/IconButton";

export { Surface } from "./surface/Surface";
export type { SurfaceElevation, SurfaceProps } from "./surface/Surface";

export { Chip } from "./chip/Chip";
export type { ChipProps, ChipTone } from "./chip/Chip";

export { VisuallyHidden } from "./visually-hidden/VisuallyHidden";
export type { VisuallyHiddenProps } from "./visually-hidden/VisuallyHidden";

export { Skeleton } from "./skeleton/Skeleton";
export type { SkeletonProps } from "./skeleton/Skeleton";

export { DesignPreview } from "./DesignPreview";
