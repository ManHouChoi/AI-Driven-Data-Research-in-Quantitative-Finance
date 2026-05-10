"use client";

import { useMemo } from "react";
import { MathText } from "@/components/ui/MathText";
import { useAttentionMatrix } from "@/lib/data/loadAttentionMatrix";
import { transformAttentionMatrixForTheta } from "@/lib/data/transformAttentionMatrix";
import { useDashboardStore } from "@/stores/useDashboardStore";

export function AttentionTooltip() {
  const { data } = useAttentionMatrix();
  const firms = data?.firms ?? [];
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const matrix = useMemo(
    () => transformAttentionMatrixForTheta(data?.matrix ?? [], theta),
    [data?.matrix, theta]
  );
  const selectedFirmId = useDashboardStore((state) => state.graph.selectedFirmId);
  const comparisonFirmId = useDashboardStore(
    (state) => state.graph.comparisonFirmId
  );
  const egoTargetFirmId = useDashboardStore(
    (state) => state.graph.egoTargetFirmId
  );
  const viewMode = useDashboardStore((state) => state.graph.viewMode);
  const threshold = useDashboardStore(
    (state) => state.graph.minAttentionThreshold
  );
  const hoveredEdge = useDashboardStore((state) => state.graph.hoveredEdge);

  if (!data) {
    return (
      <div className="rounded-lg border border-mercury-lead/20 bg-mercury-graphite p-5 text-sm text-mercury-silver">
        Loading attention readout...
      </div>
    );
  }

  const strongestEgoEdge =
    viewMode === "ego"
      ? getStrongestEgoEdge(firms, matrix, egoTargetFirmId)
      : null;
  const activeEdge = hoveredEdge ?? strongestEgoEdge;
  const activeSourceId = activeEdge?.sourceFirmId ?? selectedFirmId ?? firms[0]?.id;
  const activeTargetId = activeEdge?.targetFirmId ?? comparisonFirmId;
  const sourceIndex = firms.findIndex((firm) => firm.id === activeSourceId);
  const targetIndex = activeTargetId
    ? firms.findIndex((firm) => firm.id === activeTargetId)
    : -1;
  const sourceFirm = firms[sourceIndex] ?? firms[0];
  const row = matrix[sourceIndex] ?? matrix[0];

  const ranked = row
    .map((alpha, index) => ({
      firm: firms[index],
      alpha
    }))
    .filter((entry) => entry.firm.id !== sourceFirm.id && entry.alpha >= threshold)
    .sort((a, b) => b.alpha - a.alpha)
    .slice(0, 4);

  const activeAlpha =
    activeEdge?.alpha ??
    (targetIndex >= 0 && sourceIndex >= 0
      ? matrix[sourceIndex][targetIndex]
      : ranked[0]?.alpha ?? 0);

  return (
    <div className="rounded-lg border border-mercury-lead/20 bg-mercury-graphite p-5">
      <div className="mb-5">
        <p className="font-mono text-xs uppercase text-mercury-silver">
          Attention readout
        </p>
        <p className="mt-2 text-2xl font-normal text-mercury-starlight">
          {activeEdge ? (
            <>
              {labelFor(firms, activeEdge.sourceFirmId)}
              <span className="px-2">&rarr;</span>
              {labelFor(firms, activeEdge.targetFirmId)}
            </>
          ) : (
            sourceFirm.ticker
          )}
        </p>
      </div>

      <div className="mb-5 rounded-lg bg-apple-fog p-4">
        <p className="text-xs text-mercury-silver">
          <MathText math="\alpha_{ij}" /> weight
        </p>
        <p className="mt-1 font-mono text-4xl text-mercury-starlight">
          {activeAlpha.toFixed(3)}
        </p>
      </div>

      <div className="space-y-3">
        {ranked.map(({ firm, alpha }) => (
          <div
            className="grid grid-cols-[64px_1fr_52px] items-center gap-3 text-sm"
            key={firm.id}
          >
            <span className="font-mono text-mercury-starlight">
              {firm.ticker}
            </span>
            <span className="h-2 overflow-hidden rounded-full bg-apple-mist">
              <span
                className="block h-full rounded-full bg-mercury-ghost"
                style={{ width: `${alpha * 100}%` }}
              />
            </span>
            <span className="text-right font-mono text-mercury-silver">
              {alpha.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function labelFor(firms: Array<{ id: string; ticker: string }>, id: string) {
  return firms.find((firm) => firm.id === id)?.ticker ?? id;
}

function getStrongestEgoEdge(
  firms: Array<{ id: string }>,
  matrix: number[][],
  egoTargetFirmId: string | null
) {
  if (!egoTargetFirmId) {
    return null;
  }

  const targetIndex = firms.findIndex((firm) => firm.id === egoTargetFirmId);

  if (targetIndex < 0) {
    return null;
  }

  const targetFirm = firms[targetIndex];
  const edges = firms
    .flatMap((firm, firmIndex) => {
      if (firm.id === targetFirm.id) {
        return [];
      }

      return [
        {
          sourceFirmId: firm.id,
          targetFirmId: targetFirm.id,
          alpha: matrix[firmIndex]?.[targetIndex] ?? 0
        },
        {
          sourceFirmId: targetFirm.id,
          targetFirmId: firm.id,
          alpha: matrix[targetIndex]?.[firmIndex] ?? 0
        }
      ];
    })
    .sort((a, b) => b.alpha - a.alpha);

  return edges[0] ?? null;
}
