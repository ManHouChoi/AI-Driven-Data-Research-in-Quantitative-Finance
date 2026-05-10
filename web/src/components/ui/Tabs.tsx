"use client";

import clsx from "clsx";

interface TabOption<T extends string> {
  value: T;
  label: string;
}

interface TabsProps<T extends string> {
  value: T;
  options: TabOption<T>[];
  onChange: (value: T) => void;
}

export function Tabs<T extends string>({
  value,
  options,
  onChange
}: TabsProps<T>) {
  return (
    <div className="inline-flex rounded-full bg-apple-fog p-1" role="group">
      {options.map((option) => (
        <button
          aria-pressed={value === option.value}
          className={clsx(
            "rounded-full px-4 py-2 text-xs font-medium transition",
            value === option.value
              ? "bg-apple-ink text-white"
              : "text-apple-graphite hover:text-apple-ink"
          )}
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
