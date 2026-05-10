import { type HTMLAttributes } from "react";
import clsx from "clsx";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  tone?: "dark" | "light" | "frosted";
}

export function Card({ className, tone = "dark", ...props }: CardProps) {
  return (
    <div
      className={clsx(
        "border",
        tone === "dark" &&
          "border-mercury-lead/20 bg-mercury-slate text-mercury-starlight",
        tone === "light" &&
          "chart-surface border-apple-mist text-apple-ink",
        tone === "frosted" &&
          "frosted border-mercury-ghost/10 text-mercury-starlight",
        "rounded-lg",
        className
      )}
      {...props}
    />
  );
}
