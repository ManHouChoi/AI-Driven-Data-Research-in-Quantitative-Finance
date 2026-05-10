"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { Button } from "@/components/ui/Button";
import { usePortfolioReturns } from "@/lib/data/loadPortfolioReturns";
import { transformPortfolioSeries } from "@/lib/data/transformPortfolioSeries";
import { chartColors } from "@/lib/constants/colors";
import { useDashboardStore } from "@/stores/useDashboardStore";
import { usePortfolioStore } from "@/stores/usePortfolioStore";
import type { PortfolioLegMode } from "@/types/portfolio";

const legModeOptions: Array<{ value: PortfolioLegMode; label: string }> = [
  { value: "net", label: "Net Spread (Long/Short)" },
  { value: "long", label: "Long Leg Only" },
  { value: "short", label: "Short Leg Only" }
];

const legModeLabels: Record<PortfolioLegMode, string> = {
  net: "Net spread",
  long: "Long leg",
  short: "Short leg"
};

export function EquityCurveChart() {
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const signalWeights = usePortfolioStore((state) => state.signalWeights);
  const riskControls = usePortfolioStore((state) => state.riskControls);
  const selectedLegMode = usePortfolioStore((state) => state.selectedLegMode);
  const setSelectedLegMode = usePortfolioStore((state) => state.setSelectedLegMode);
  const { data: returns, isLoading } = usePortfolioReturns();

  const data = useMemo(
    () =>
      transformPortfolioSeries(
        returns,
        signalWeights,
        riskControls,
        theta,
        selectedLegMode
      ).map((point) => ({
        ...point,
        stgatReturn: point.stgat - 1,
        spyReturn: point.spy - 1,
        compositeReturn: point.composite - 1,
        selectedLegReturn: point.selectedLeg - 1,
        netSpreadReturn: point.netSpread - 1,
        longLegReturn: point.longLeg - 1,
        shortLegReturn: point.shortLeg - 1
      })),
    [returns, riskControls, selectedLegMode, signalWeights, theta]
  );

  if (isLoading) {
    return (
      <div className="flex h-[500px] items-center justify-center text-sm text-apple-graphite">
        Loading portfolio returns...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {legModeOptions.map((option) => (
          <Button
            aria-pressed={selectedLegMode === option.value}
            className="min-w-[160px]"
            key={option.value}
            variant={selectedLegMode === option.value ? "primary" : "secondary"}
            onClick={() => setSelectedLegMode(option.value)}
          >
            {option.label}
          </Button>
        ))}
      </div>

      <div className="h-[460px] w-full">
        <ResponsiveContainer height="100%" width="100%">
          <LineChart data={data} margin={{ bottom: 12, left: 8, right: 28, top: 24 }}>
            <CartesianGrid stroke="#ededf3" vertical={false} />
            <XAxis
              dataKey="date"
              interval={5}
              stroke={chartColors.ink}
              tick={{ fill: chartColors.ink, fontSize: 12 }}
              tickLine={false}
            />
            <YAxis
              stroke={chartColors.ink}
              tick={{ fill: chartColors.ink, fontSize: 12 }}
              tickFormatter={(value) => `${(Number(value) * 100).toFixed(0)}%`}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: chartColors.ink,
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: chartColors.starlight
              }}
              formatter={(value: number, name: string) => [
                `${(value * 100).toFixed(1)}%`,
                name
              ]}
              labelStyle={{ color: chartColors.starlight }}
            />
            <Legend />
            <Line
              dataKey="compositeReturn"
              dot={false}
              name="Dynamic blend"
              stroke={chartColors.mercuryBlue}
              strokeWidth={3}
              type="monotone"
            />
            <Line
              dataKey="selectedLegReturn"
              dot={false}
              name={legModeLabels[selectedLegMode]}
              stroke={chartColors.teal}
              strokeWidth={2}
              type="monotone"
            />
            <Line
              dataKey="spyReturn"
              dot={false}
              name="SPY"
              stroke={chartColors.ink}
              strokeWidth={2}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs leading-relaxed text-apple-graphite">
        Metrics are net of 15 bps turnover friction. Signal formed on Year{" "}
        <span className="font-mono">t</span> disclosures; applied strictly to July{" "}
        <span className="font-mono">t+1</span> - June{" "}
        <span className="font-mono">t+2</span> to eliminate look-ahead bias.
      </p>
    </div>
  );
}
