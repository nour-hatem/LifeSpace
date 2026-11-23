import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

import styles from "./IconButton.module.css";

/** Props for the IconButton; the accessible label is required. */
export type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  children: ReactNode;
};

/**
 * Square icon-only button that exposes its required label as the accessible
 * name and hides the icon from assistive technology (ADR 0003 item 14).
 */
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, children, type = "button", className, ...rest },
  ref,
) {
  return (
    <button
      {...rest}
      ref={ref}
      type={type}
      aria-label={label}
      className={[styles.iconButton, className].filter(Boolean).join(" ")}
    >
      <span aria-hidden="true" className={styles.icon}>
        {children}
      </span>
    </button>
  );
});
