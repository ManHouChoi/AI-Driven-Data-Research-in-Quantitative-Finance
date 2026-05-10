"use client";

import { MathText } from "@/components/ui/MathText";
import { useDashboardStore } from "@/stores/useDashboardStore";
import type { TaxonomyTheta } from "@/types/taxonomy";

export function ThetaSensitivitySlider() {
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const setTheta = useDashboardStore((state) => state.setTheta);

  const sliderValue = theta === 0.45 ? 0 : 1;

  return (
    <div className="rounded-lg border border-mercury-lead/20 bg-mercury-graphite p-4">
      <div className="mb-3 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-mercury-starlight">
            Sensitivity path
          </p>
          <p className="mt-1 font-mono text-xs text-mercury-silver">
            <MathText math={`\\theta=${theta.toFixed(2)}`} />
          </p>
        </div>
        <span className="rounded-full bg-mercury-ghost/10 px-3 py-1 font-mono text-xs">
          {theta === 0.45 ? "default" : "sensitive"}
        </span>
      </div>
      <input
        className="h-2 w-full accent-mercury-blue"
        max={1}
        min={0}
        step={1}
        type="range"
        value={sliderValue}
        onChange={(event) => {
          const next: TaxonomyTheta =
            Number(event.target.value) === 0 ? 0.45 : 0.4;
          setTheta(next);
        }}
      />
      <div className="mt-2 flex justify-between font-mono text-xs text-mercury-silver">
        <span>0.45</span>
        <span>0.40</span>
      </div>
    </div>
  );
}
