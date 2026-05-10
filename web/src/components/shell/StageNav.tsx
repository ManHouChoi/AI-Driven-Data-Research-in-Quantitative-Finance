"use client";

import clsx from "clsx";
import { stages } from "@/lib/constants/stages";
import { useDashboardStore } from "@/stores/useDashboardStore";

export function StageNav() {
  const activeStage = useDashboardStore((state) => state.activeStage);
  const setActiveStage = useDashboardStore((state) => state.setActiveStage);

  return (
    <nav className="sticky top-0 z-40 border-b border-apple-mist bg-white/86 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <a className="flex items-center gap-3" href="#data-pipeline">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-mercury-blue text-xs font-semibold text-white">
            QF
          </span>
          <span className="hidden text-sm font-medium text-mercury-starlight sm:inline">
            Quant Finance Research Demo
          </span>
        </a>
        <div className="thin-scrollbar flex max-w-[72vw] gap-2 overflow-x-auto rounded-full bg-apple-fog p-1">
          {stages.map(({ id, label, kicker, Icon }) => (
            <a
              className={clsx(
                "flex shrink-0 items-center gap-2 rounded-full px-3 py-2 text-xs transition sm:px-4",
                activeStage === id
                  ? "bg-apple-ink text-white"
                  : "text-apple-graphite hover:text-apple-ink"
              )}
              href={`#${id}`}
              key={id}
              onClick={() => setActiveStage(id)}
            >
              <Icon className="h-4 w-4" />
              <span className="font-mono">{kicker}</span>
              <span>{label}</span>
            </a>
          ))}
        </div>
      </div>
    </nav>
  );
}
