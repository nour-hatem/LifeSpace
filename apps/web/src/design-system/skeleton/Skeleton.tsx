import type { CSSProperties } from "react";

import styles from "./Skeleton.module.css";

/** Props for the Skeleton loading block. */
export type SkeletonProps = {
  width?: CSSProperties["width"];
  height?: CSSProperties["height"];
  className?: string;
};

/**
 * Decorative loading placeholder with a shimmer that becomes a static block
 * under prefers-reduced-motion (ADR 0003 items 7 and 12).
 */
export function Skeleton({ width = "100%", height = 16, className }: SkeletonProps) {
  return (
    <span
      aria-hidden="true"
      className={[styles.skeleton, className].filter(Boolean).join(" ")}
      style={{ width, height }}
    />
  );
}
