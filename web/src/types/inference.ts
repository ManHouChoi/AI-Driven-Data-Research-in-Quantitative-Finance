export type InferenceStatus = "idle" | "loading" | "success" | "error";

export interface TaxonomyPrediction {
  label: string;
  score: number;
  similarity: number;
  level: "meso" | "macro";
}

export interface RiskClassificationResult {
  meso: TaxonomyPrediction[];
  macro: TaxonomyPrediction[];
  topSimilarity: number;
  explanation: string;
  timestamp: string;
}

export interface ClassifyRiskRequest {
  text: string;
}

export interface ClassifyRiskResponse extends RiskClassificationResult {
  requestId: string;
}
