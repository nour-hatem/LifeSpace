import type { HTMLAttributes, ReactNode } from "react";

import styles from "./VisuallyHidden.module.css";

/** Props for VisuallyHidden. */
export type VisuallyHiddenProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode;
};

/**
 * Hides content visually while keeping it available to assistive technology
 * (ADR 0003 item 14).
 */
export function VisuallyHidden({ className, children, ...rest }: VisuallyHiddenProps) {
  return (
    <span {...rest} className={[styles.visuallyHidden, className].filter(Boolean).join(" ")}>
      {children}
    </span>
  );
}
