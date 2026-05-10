"use client";

import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Slider } from "@/components/ui/Slider";
import { Tabs } from "@/components/ui/Tabs";
import { usePortfolioStore } from "@/stores/usePortfolioStore";
import type { PortfolioMetric, RebalanceFrequency } from "@/types/portfolio";

export function SignalWeightControls() {
  const signalWeights = usePortfolioStore((state) => state.signalWeights);
  const riskControls = usePortfolioStore((state) => state.riskControls);
  const selectedMetric = usePortfolioStore((state) => state.selectedMetric);
  const setSignalWeight = usePortfolioStore((state) => state.setSignalWeight);
  const setRiskControl = usePortfolioStore((state) => state.setRiskControl);
  const setSelectedMetric = usePortfolioStore((state) => state.setSelectedMetric);
  const resetPortfolioControls = usePortfolioStore(
    (state) => state.resetPortfolioControls
  );

  return (
    <div className="space-y-5 rounded-lg border border-mercury-lead/20 bg-mercury-graphite p-5">
      <div>
        <p className="text-sm font-medium text-mercury-starlight">
          Signal mix
        </p>
        <p className="mt-1 text-xs text-mercury-silver">
          Portfolio hyperparameters
        </p>
      </div>

      <div className="space-y-4">
        <Slider
          label="ST-GAT signal"
          max={1}
          min={0}
          value={signalWeights.stgatSignal}
          onChange={(value) => setSignalWeight("stgatSignal", value)}
        />
        <Slider
          label="NLP risk signal"
          max={1}
          min={0}
          value={signalWeights.nlpRiskSignal}
          onChange={(value) => setSignalWeight("nlpRiskSignal", value)}
        />
        <Slider
          label="Momentum signal"
          max={1}
          min={0}
          value={signalWeights.momentumSignal}
          onChange={(value) => setSignalWeight("momentumSignal", value)}
        />
        <Slider
          label="Volatility penalty"
          max={1}
          min={0}
          value={signalWeights.volatilityPenalty}
          onChange={(value) => setSignalWeight("volatilityPenalty", value)}
        />
        <Slider
          label="Max gross exposure"
          max={2}
          min={0.2}
          value={riskControls.maxGrossExposure}
          onChange={(value) => setRiskControl("maxGrossExposure", value)}
        />
        <Slider
          label="Transaction cost"
          max={30}
          min={0}
          step={1}
          suffix=" bps"
          value={riskControls.transactionCostBps}
          onChange={(value) => setRiskControl("transactionCostBps", value)}
        />
      </div>

      <label className="block">
        <span className="mb-2 block text-xs text-mercury-silver">
          Rebalance
        </span>
        <Select
          className="w-full"
          value={riskControls.rebalanceFrequency}
          onChange={(event) =>
            setRiskControl(
              "rebalanceFrequency",
              event.target.value as RebalanceFrequency
            )
          }
        >
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
        </Select>
      </label>

      <Tabs<PortfolioMetric>
        options={[
          { value: "cumulativeReturn", label: "Return" },
          { value: "sharpe", label: "Sharpe" },
          { value: "drawdown", label: "Drawdown" },
          { value: "volatility", label: "Vol" }
        ]}
        value={selectedMetric}
        onChange={setSelectedMetric}
      />

      <Button
        className="w-full"
        icon={<RotateCcw className="h-4 w-4" />}
        variant="secondary"
        onClick={resetPortfolioControls}
      >
        Reset controls
      </Button>
    </div>
  );
}
