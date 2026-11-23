import type { HTMLAttributes, ReactNode } from "react";

import styles from "./Chip.module.css";

/** Semantic tones of the Chip (ADR 0003 items 3 and 8). */
export type ChipTone = "neutral" | "primary" | "success" | "warning" | "danger" | "violet";

/** Props for the Chip; the text children are required. */
export type ChipProps = Omit<HTMLAttributes<HTMLSpanElement>, "children"> & {
  tone?: ChipTone;
  icon?: ReactNode;
  children: ReactNode;
};

/**
 * Small status label: a tone color at 16 percent over the surface with a
 * contrasting text token (ADR 0003 items 3 and 8). The visible text always
 * carries the meaning, so color is never the only signal.
 */
export function Chip({ tone = "neutral", icon, className, children, ...rest }: ChipProps) {
  return (
    <span {...rest} className={[styles.chip, styles[tone], className].filter(Boolean).join(" ")}>
      {icon ? (
        <span className={styles.icon} aria-hidden="true">
          {icon}
        </span>
      ) : null}
      {children}
    </span>
  );
}
