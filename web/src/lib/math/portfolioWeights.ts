import type {
  PortfolioReturnPoint,
  PortfolioSignalWeights,
  PortfolioRiskControls
} from "@/types/portfolio";

export function combineSignals(
  point: PortfolioReturnPoint,
  weights: PortfolioSignalWeights,
  controls: PortfolioRiskControls
): number {
  const signalTotal =
    weights.stgatSignal + weights.nlpRiskSignal + weights.momentumSignal;

  const normalizedTotal = signalTotal === 0 ? 1 : signalTotal;

  const grossSignal =
    (point.stgat * weights.stgatSignal +
      point.nlpRisk * weights.nlpRiskSignal +
      point.momentum * weights.momentumSignal) /
    normalizedTotal;

  const exposureAdjusted = grossSignal * controls.maxGrossExposure;
  const volatilityDrag = point.volatility * weights.volatilityPenalty * 0.18;
  const monthlyTurnoverCost =
    controls.transactionCostBps / 10000 / (controls.rebalanceFrequency === "monthly" ? 1 : 3);

  return exposureAdjusted - volatilityDrag - monthlyTurnoverCost;
}
