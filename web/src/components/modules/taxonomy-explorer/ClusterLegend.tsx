"use client";

import clsx from "clsx";
import { clusterSummaries } from "@/lib/constants/taxonomy";
import { useDashboardStore } from "@/stores/useDashboardStore";

export function ClusterLegend() {
  const selectedClusterId = useDashboardStore(
    (state) => state.taxonomy.selectedClusterId
  );
  const setSelectedClusterId = useDashboardStore(
    (state) => state.setSelectedClusterId
  );

  return (
    <div className="rounded-lg border border-mercury-lead/20 bg-mercury-graphite p-4">
      <div className="mb-3">
        <p className="text-sm font-medium text-mercury-starlight">
          Meso cluster filter
        </p>
        <p className="mt-1 text-xs text-mercury-silver">
          Applies to the sparse meso topology panels.
        </p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
        {clusterSummaries.map((cluster) => {
          const selected = selectedClusterId === cluster.id;

          return (
            <button
              className={clsx(
                "flex items-center justify-between gap-4 rounded-lg border p-3 text-left transition",
                selected
                  ? "border-mercury-ghost/60 bg-mercury-ghost/10"
                  : "border-mercury-lead/20 bg-mercury-slate hover:border-mercury-ghost/30"
              )}
              key={cluster.id}
              type="button"
              onClick={() =>
                setSelectedClusterId(selected ? null : cluster.id)
              }
            >
              <span className="flex min-w-0 items-center gap-3">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: cluster.color }}
                />
                <span className="min-w-0">
                  <span className="block truncate text-sm text-mercury-starlight">
                    {cluster.label}
                  </span>
                  <span className="block truncate text-xs text-mercury-silver">
                    {cluster.parent}
                  </span>
                </span>
              </span>
              <span className="font-mono text-xs text-mercury-silver">
                {cluster.count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
