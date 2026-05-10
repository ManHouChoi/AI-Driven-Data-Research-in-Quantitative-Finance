"use client";

import { useEffect } from "react";
import { AttentionHeatmap } from "@/components/modules/st-gat-graph/AttentionHeatmap";
import { AttentionTooltip } from "@/components/modules/st-gat-graph/AttentionTooltip";
import { EgoNetworkGraph } from "@/components/modules/st-gat-graph/EgoNetworkGraph";
import { FirmSelector } from "@/components/modules/st-gat-graph/FirmSelector";
import { SectionHeader } from "@/components/shell/SectionHeader";
import { Card } from "@/components/ui/Card";
import { MathText } from "@/components/ui/MathText";
import { Select } from "@/components/ui/Select";
import { Slider } from "@/components/ui/Slider";
import { Tabs } from "@/components/ui/Tabs";
import { useAttentionMatrix } from "@/lib/data/loadAttentionMatrix";
import { useDashboardStore } from "@/stores/useDashboardStore";
import type { GraphViewMode } from "@/types/graph";

export function STGATGraphSection() {
  const { data } = useAttentionMatrix();
  const firms = data?.firms ?? [];
  const threshold = useDashboardStore(
    (state) => state.graph.minAttentionThreshold
  );
  const viewMode = useDashboardStore((state) => state.graph.viewMode);
  const egoTargetFirmId = useDashboardStore(
    (state) => state.graph.egoTargetFirmId
  );
  const setThreshold = useDashboardStore(
    (state) => state.setMinAttentionThreshold
  );
  const setViewMode = useDashboardStore((state) => state.setGraphViewMode);
  const setEgoTargetFirmId = useDashboardStore(
    (state) => state.setEgoTargetFirmId
  );
  const setHoveredEdge = useDashboardStore((state) => state.setHoveredEdge);

  useEffect(() => {
    if (viewMode === "ego") {
      setHoveredEdge(null);
    }
  }, [setHoveredEdge, viewMode]);

  return (
    <section
      className="border-b border-mercury-lead/20 bg-mercury-slate px-4 py-20 sm:px-6 lg:px-8"
      id="graph"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-10 flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <SectionHeader
            copy="The ST-GAT layer exposes firm-to-firm attention weights used by the forecasting model."
            kicker="06 / Spatio-Temporal Graph"
            title="Firm attention matrix"
          />
          <Tabs<GraphViewMode>
            options={[
              { value: "matrix", label: "Matrix View" },
              { value: "ego", label: "Ego-Network View" }
            ]}
            value={viewMode}
            onChange={setViewMode}
          />
        </div>

        <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
          <aside className="space-y-5">
            {viewMode === "matrix" ? (
              <>
                <FirmSelector />
                <Slider
                  label={
                    <>
                      Minimum <MathText math="\alpha_{ij}" />
                    </>
                  }
                  max={0.5}
                  min={0}
                  step={0.01}
                  value={threshold}
                  onChange={setThreshold}
                />
              </>
            ) : (
              <div className="rounded-lg border border-mercury-lead/20 bg-mercury-graphite p-5">
                <label>
                  <span className="mb-2 block text-xs text-mercury-silver">
                    Target firm
                  </span>
                  <Select
                    className="w-full"
                    disabled={!data}
                    value={egoTargetFirmId ?? firms[0]?.id ?? ""}
                    onChange={(event) => {
                      setHoveredEdge(null);
                      setEgoTargetFirmId(event.target.value || null);
                    }}
                  >
                    {firms.map((firm) => (
                      <option key={firm.id} value={firm.id}>
                        {firm.ticker} · {firm.sector}
                      </option>
                    ))}
                  </Select>
                </label>
                <p className="mt-4 text-sm leading-6 text-mercury-silver">
                  Shows the top 5 attention sources pointing to the target and
                  the top 5 targets receiving attention from it.
                </p>
              </div>
            )}
            <AttentionTooltip />
          </aside>
          <Card className="overflow-hidden p-2" tone="light">
            {viewMode === "matrix" ? <AttentionHeatmap /> : <EgoNetworkGraph />}
          </Card>
        </div>
      </div>
    </section>
  );
}
