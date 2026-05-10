"use client";

import { create } from "zustand";
import type {
  PortfolioLegMode,
  PortfolioMetric,
  PortfolioRiskControls,
  PortfolioSignalWeights
} from "@/types/portfolio";

export interface PortfolioHyperparameterState {
  signalWeights: PortfolioSignalWeights;
  riskControls: PortfolioRiskControls;
  selectedMetric: PortfolioMetric;
  selectedLegMode: PortfolioLegMode;
  setSignalWeight: (key: keyof PortfolioSignalWeights, value: number) => void;
  setRiskControl: <K extends keyof PortfolioRiskControls>(
    key: K,
    value: PortfolioRiskControls[K]
  ) => void;
  setSelectedMetric: (metric: PortfolioMetric) => void;
  setSelectedLegMode: (mode: PortfolioLegMode) => void;
  resetPortfolioControls: () => void;
}

const defaultSignalWeights: PortfolioSignalWeights = {
  stgatSignal: 0.58,
  nlpRiskSignal: 0.24,
  momentumSignal: 0.18,
  volatilityPenalty: 0.35
};

const defaultRiskControls: PortfolioRiskControls = {
  maxGrossExposure: 1.2,
  rebalanceFrequency: "monthly",
  transactionCostBps: 15
};

export const usePortfolioStore = create<PortfolioHyperparameterState>((set) => ({
  signalWeights: defaultSignalWeights,
  riskControls: defaultRiskControls,
  selectedMetric: "cumulativeReturn",
  selectedLegMode: "net",
  setSignalWeight: (key, value) =>
    set((state) => ({
      signalWeights: {
        ...state.signalWeights,
        [key]: value
      }
    })),
  setRiskControl: (key, value) =>
    set((state) => ({
      riskControls: {
        ...state.riskControls,
        [key]: value
      }
    })),
  setSelectedMetric: (selectedMetric) => set({ selectedMetric }),
  setSelectedLegMode: (selectedLegMode) => set({ selectedLegMode }),
  resetPortfolioControls: () =>
    set({
      signalWeights: defaultSignalWeights,
      riskControls: defaultRiskControls,
      selectedMetric: "cumulativeReturn",
      selectedLegMode: "net"
    })
}));
