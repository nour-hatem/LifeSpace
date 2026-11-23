import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

import styles from "./Button.module.css";

/** Visual variants of the Button (ADR 0003 items 2, 3, and 14). */
export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

/** Touch-safe sizes of the Button (ADR 0003 item 14). */
export type ButtonSize = "md" | "lg";

/** Props for the Button; every native button attribute is accepted. */
export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children?: ReactNode;
};

/**
 * Accessible button with the approved variants and sizes (ADR 0003 items 2,
 * 3, 7, and 14). While loading it is disabled, marked aria-busy, and shows a
 * spinner plus the visible text "Working".
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = "primary",
    size = "md",
    loading = false,
    disabled = false,
    type = "button",
    className,
    children,
    ...rest
  },
  ref,
) {
  const classes = [styles.button, styles[variant], styles[size], className]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      {...rest}
      ref={ref}
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      {loading ? (
        <>
          <span className={styles.spinner} aria-hidden="true" />
          <span>Working</span>
        </>
      ) : (
        children
      )}
    </button>
  );
});
