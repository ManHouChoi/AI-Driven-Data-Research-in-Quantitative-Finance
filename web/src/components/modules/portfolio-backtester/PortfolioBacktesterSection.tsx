"use client";

import { EquityCurveChart } from "@/components/modules/portfolio-backtester/EquityCurveChart";
import { PerformanceStats } from "@/components/modules/portfolio-backtester/PerformanceStats";
import { SignalWeightControls } from "@/components/modules/portfolio-backtester/SignalWeightControls";
import { SectionHeader } from "@/components/shell/SectionHeader";
import { Card } from "@/components/ui/Card";

export function PortfolioBacktesterSection() {
  return (
    <section
      className="bg-mercury-abyss px-4 py-20 sm:px-6 lg:px-8"
      id="portfolio"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-10">
          <SectionHeader
            copy="The portfolio stage compares the theta-conditioned ST-GAT signal against SPY, with leg decomposition and live signal weights."
            kicker="07 / Backtest"
            title="Signal-weighted portfolio"
          />
        </div>

        <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
          <SignalWeightControls />
          <Card className="space-y-4 overflow-hidden p-4" tone="light">
            <PerformanceStats />
            <EquityCurveChart />
          </Card>
        </div>
      </div>
    </section>
  );
}
