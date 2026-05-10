"use client";

import type { SelectHTMLAttributes } from "react";
import clsx from "clsx";

export function Select({
  className,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={clsx(
        "h-10 rounded-full border border-apple-mist bg-white px-4 text-sm text-apple-ink outline-none focus:border-mercury-blue/60",
        className
      )}
      {...props}
    />
  );
}
