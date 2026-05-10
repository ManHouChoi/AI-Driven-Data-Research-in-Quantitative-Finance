"use client";

import { type ReactNode } from "react";
import clsx from "clsx";

interface SliderProps {
  label: ReactNode;
  value: number;
  min: number;
  max: number;
  step?: number;
  suffix?: string;
  onChange: (value: number) => void;
  className?: string;
}

export function Slider({
  label,
  value,
  min,
  max,
  step = 0.01,
  suffix = "",
  onChange,
  className
}: SliderProps) {
  return (
    <label className={clsx("block", className)}>
      <span className="mb-2 flex items-center justify-between gap-4 text-xs text-mercury-silver">
        <span>{label}</span>
        <span className="font-mono text-mercury-starlight">
          {value.toFixed(step >= 1 ? 0 : 2)}
          {suffix}
        </span>
      </span>
      <input
        className="h-2 w-full accent-mercury-blue"
        max={max}
        min={min}
        step={step}
        type="range"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}
