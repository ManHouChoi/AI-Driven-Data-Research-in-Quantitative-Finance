export interface Firm {
  id: string;
  ticker: string;
  name: string;
  sector: string;
}

export interface AttentionEdge {
  sourceFirmId: string;
  targetFirmId: string;
  alpha: number;
}

export interface AttentionMatrixData {
  firms: Firm[];
  matrix: number[][];
}

export type GraphViewMode = "matrix" | "ego";
