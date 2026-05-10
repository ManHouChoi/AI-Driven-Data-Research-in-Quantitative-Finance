export type RebalanceFrequency = "monthly" | "quarterly";
export type PortfolioLegMode = "net" | "long" | "short";

export interface PortfolioReturnPoint {
  date: string;
  stgat: number;
  spy: number;
  nlpRisk: number;
  momentum: number;
  volatility: number;
}

export interface PortfolioEquityPoint {
  date: string;
  stgat: number;
  spy: number;
  composite: number;
  netSpread: number;
  longLeg: number;
  shortLeg: number;
  selectedLeg: number;
}

export interface PerformanceStats {
  cumulativeReturn: number;
  sharpe: number;
  volatility: number;
  maxDrawdown: number;
}

export interface PortfolioSignalWeights {
  stgatSignal: number;
  nlpRiskSignal: number;
  momentumSignal: number;
  volatilityPenalty: number;
}

export interface PortfolioRiskControls {
  maxGrossExposure: number;
  rebalanceFrequency: RebalanceFrequency;
  transactionCostBps: number;
}

export type PortfolioMetric =
  | "cumulativeReturn"
  | "sharpe"
  | "drawdown"
  | "volatility";

export interface CaseStudyPeer {
  ticker: string;
  cosine: number;
  x: number;
  y: number;
}

export interface CaseStudyPoint {
  year: number;
  macroCategory: string;
  macroShare: number;
  mesoCategory: string;
  mesoShare: number;
  vectorDistance: number;
  nearestPeer: string;
  nearestPeerCosine: number;
  x: number;
  y: number;
  peers: CaseStudyPeer[];
}

export interface CaseStudyTicker {
  ticker: string;
  name: string;
  archetype?: string;
  shockYears: number[];
  trajectory: CaseStudyPoint[];
}

export interface CaseStudyData {
  tickers: CaseStudyTicker[];
}
