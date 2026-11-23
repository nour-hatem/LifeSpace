import type { HTMLAttributes, ReactNode } from "react";

import styles from "./Surface.module.css";

/** Elevation options for the Surface (ADR 0003 item 6). */
export type SurfaceElevation = "flat" | "floating";

/** Props for the Surface. */
export type SurfaceProps = HTMLAttributes<HTMLDivElement> & {
  elevation?: SurfaceElevation;
  children?: ReactNode;
};

/**
 * Panel container with the approved flat or floating treatment (ADR 0003
 * item 6). Floating surfaces become opaque when backdrop blur is unsupported
 * or reduced transparency is requested.
 */
export function Surface({ elevation = "flat", className, children, ...rest }: SurfaceProps) {
  return (
    <div
      {...rest}
      className={[styles.surface, styles[elevation], className].filter(Boolean).join(" ")}
    >
      {children}
    </div>
  );
}
