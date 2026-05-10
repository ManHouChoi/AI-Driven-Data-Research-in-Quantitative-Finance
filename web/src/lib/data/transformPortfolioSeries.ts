import { combineSignals } from "@/lib/math/portfolioWeights";
import type {
  PortfolioEquityPoint,
  PortfolioLegMode,
  PortfolioReturnPoint,
  PortfolioRiskControls,
  PortfolioSignalWeights
} from "@/types/portfolio";
import type { TaxonomyTheta } from "@/types/taxonomy";

export function transformPortfolioSeries(
  returns: PortfolioReturnPoint[],
  weights: PortfolioSignalWeights,
  controls: PortfolioRiskControls,
  theta: TaxonomyTheta = 0.45,
  selectedLegMode: PortfolioLegMode = "net"
): PortfolioEquityPoint[] {
  let stgat = 1;
  let spy = 1;
  let composite = 1;
  let netSpread = 1;
  let longLeg = 1;
  let shortLeg = 1;

  return returns.map((point) => {
    const thetaLift = theta === 0.4 ? 1.1 : 1;
    const thetaRiskTilt = theta === 0.4 ? point.nlpRisk * 0.12 - point.volatility * 0.015 : 0;
    const turnoverCost =
      controls.transactionCostBps /
      10000 /
      (controls.rebalanceFrequency === "monthly" ? 1 : 3);
    const netSpreadReturn = point.stgat * thetaLift + thetaRiskTilt - turnoverCost;
    const longLegReturn =
      point.spy * 0.42 +
      point.stgat * 0.58 * thetaLift +
      point.nlpRisk * 0.16 +
      point.momentum * 0.1 -
      turnoverCost * 0.5;
    const shortLegReturn =
      -point.spy * 0.28 +
      point.stgat * 0.42 * thetaLift +
      point.nlpRisk * 0.1 -
      point.volatility * 0.04 -
      turnoverCost * 0.5;
    stgat *= 1 + netSpreadReturn;
    spy *= 1 + point.spy;
    composite *= 1 + combineSignals(point, weights, controls) * thetaLift + thetaRiskTilt;
    netSpread *= 1 + netSpreadReturn;
    longLeg *= 1 + longLegReturn;
    shortLeg *= 1 + shortLegReturn;

    return {
      date: point.date,
      stgat,
      spy,
      composite,
      netSpread,
      longLeg,
      shortLeg,
      selectedLeg:
        selectedLegMode === "long"
          ? longLeg
          : selectedLegMode === "short"
            ? shortLeg
            : netSpread
    };
  });
}
