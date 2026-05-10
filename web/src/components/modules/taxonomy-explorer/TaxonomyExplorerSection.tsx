"use client";

import { ClusterLegend } from "@/components/modules/taxonomy-explorer/ClusterLegend";
import { ThetaSensitivitySlider } from "@/components/modules/taxonomy-explorer/ThetaSensitivitySlider";
import { TopologyComparisonGrid } from "@/components/modules/taxonomy-explorer/TopologyComparisonGrid";
import { SectionHeader } from "@/components/shell/SectionHeader";

export function TaxonomyExplorerSection() {
  return (
    <section
      className="border-b border-mercury-lead/20 bg-mercury-abyss px-4 py-20 sm:px-6 lg:px-8"
      id="taxonomy"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-10">
          <SectionHeader
            copy="Broad macro labels create a denser risk surface, while finer meso labels separate exposures into fewer surviving semantic links. Both levels are shown in 2D and 3D UMAP topology views."
            kicker="05 / Macro vs Meso Topology"
            title="Dynamic risk taxonomy"
          />
        </div>

        <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-5">
            <ThetaSensitivitySlider />
            <ClusterLegend />
          </aside>
          <TopologyComparisonGrid />
        </div>
      </div>
    </section>
  );
}
