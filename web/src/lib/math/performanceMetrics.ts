import type { PerformanceStats, PortfolioEquityPoint } from "@/types/portfolio";

export function toPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatRatio(value: number): string {
  return value.toFixed(2);
}

export function calculateStats(
  equity: PortfolioEquityPoint[],
  key: keyof Pick<
    PortfolioEquityPoint,
    | "stgat"
    | "spy"
    | "composite"
    | "netSpread"
    | "longLeg"
    | "shortLeg"
    | "selectedLeg"
  >
): PerformanceStats {
  if (equity.length < 2) {
    return {
      cumulativeReturn: 0,
      sharpe: 0,
      volatility: 0,
      maxDrawdown: 0
    };
  }

  const returns = equity.slice(1).map((point, index) => {
    const previous = equity[index][key];
    return previous === 0 ? 0 : point[key] / previous - 1;
  });

  const cumulativeReturn = equity[equity.length - 1][key] - 1;
  const mean = returns.reduce((sum, value) => sum + value, 0) / returns.length;
  const variance =
    returns.reduce((sum, value) => sum + (value - mean) ** 2, 0) /
    Math.max(returns.length - 1, 1);
  const monthlyVolatility = Math.sqrt(variance);
  const volatility = monthlyVolatility * Math.sqrt(12);
  const sharpe = volatility === 0 ? 0 : (mean * 12) / volatility;

  let peak = equity[0][key];
  let maxDrawdown = 0;

  for (const point of equity) {
    peak = Math.max(peak, point[key]);
    const drawdown = peak === 0 ? 0 : point[key] / peak - 1;
    maxDrawdown = Math.min(maxDrawdown, drawdown);
  }

  return {
    cumulativeReturn,
    sharpe,
    volatility,
    maxDrawdown
  };
}
