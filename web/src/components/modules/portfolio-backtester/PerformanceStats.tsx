"use client";

import { useMemo } from "react";
import { calculateStats, formatRatio, toPercent } from "@/lib/math/performanceMetrics";
import { usePortfolioReturns } from "@/lib/data/loadPortfolioReturns";
import { transformPortfolioSeries } from "@/lib/data/transformPortfolioSeries";
import { useDashboardStore } from "@/stores/useDashboardStore";
import { usePortfolioStore } from "@/stores/usePortfolioStore";

const legModeLabels = {
  net: "Net spread",
  long: "Long leg",
  short: "Short leg"
} as const;

export function PerformanceStats() {
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const signalWeights = usePortfolioStore((state) => state.signalWeights);
  const riskControls = usePortfolioStore((state) => state.riskControls);
  const selectedMetric = usePortfolioStore((state) => state.selectedMetric);
  const selectedLegMode = usePortfolioStore((state) => state.selectedLegMode);
  const { data: returns, isLoading } = usePortfolioReturns();

  const stats = useMemo(() => {
    const equity = transformPortfolioSeries(
      returns,
      signalWeights,
      riskControls,
      theta,
      selectedLegMode
    );

    return [
      {
        label: legModeLabels[selectedLegMode],
        value: calculateStats(equity, "selectedLeg")
      },
      {
        label: "Dynamic blend",
        value: calculateStats(equity, "composite")
      },
      {
        label: "SPY",
        value: calculateStats(equity, "spy")
      }
    ];
  }, [returns, riskControls, selectedLegMode, signalWeights, theta]);

  const metricLabels = {
    cumulativeReturn: "Cumulative return",
    sharpe: "Sharpe",
    drawdown: "Max drawdown",
    volatility: "Annualized vol"
  };

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {stats.map((entry) => {
        const rawValue =
          selectedMetric === "drawdown"
            ? entry.value.maxDrawdown
            : selectedMetric === "cumulativeReturn"
              ? entry.value.cumulativeReturn
              : selectedMetric === "sharpe"
                ? entry.value.sharpe
                : entry.value.volatility;

        const formatted =
          selectedMetric === "sharpe" ? formatRatio(rawValue) : toPercent(rawValue);

        return (
          <div
            className="rounded-lg border border-apple-mist bg-apple-fog p-4"
            key={entry.label}
          >
            <p className="text-xs text-apple-graphite">{entry.label}</p>
            <p className="mt-2 font-mono text-2xl text-apple-ink">
              {isLoading ? "--" : formatted}
            </p>
            <p className="mt-1 text-xs text-apple-graphite">
              {metricLabels[selectedMetric]}
            </p>
          </div>
        );
      })}
    </div>
  );
}
