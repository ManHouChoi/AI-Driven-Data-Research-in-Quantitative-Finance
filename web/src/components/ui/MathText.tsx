"use client";

import clsx from "clsx";
import { InlineMath } from "react-katex";

interface MathTextProps {
  math: string;
  className?: string;
}

export function MathText({ math, className }: MathTextProps) {
  return (
    <span className={clsx("inline-flex items-baseline", className)}>
      <InlineMath math={math} />
    </span>
  );
}
