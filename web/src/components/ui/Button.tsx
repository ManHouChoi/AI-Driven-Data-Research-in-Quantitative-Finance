"use client";

import { type ButtonHTMLAttributes, type ReactNode } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  icon?: ReactNode;
}

export function Button({
  children,
  className,
  variant = "secondary",
  icon,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-full px-5 py-2 text-sm font-medium transition disabled:opacity-50",
        variant === "primary" &&
          "bg-mercury-blue text-white hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-mercury-blue focus:ring-offset-2 focus:ring-offset-white",
        variant === "secondary" &&
          "bg-apple-fog text-apple-ink hover:bg-apple-mist",
        variant === "ghost" &&
          "bg-transparent px-2 text-apple-ink hover:text-apple-graphite",
        className
      )}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}
