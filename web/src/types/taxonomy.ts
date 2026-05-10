export type TaxonomyTheta = 0.45 | 0.4;

export type ProjectionMode = "2d" | "3d";

export type TaxonomyTopologyLevel = "macro" | "meso";

export interface UMAPPoint {
  id: string;
  label: string;
  parent: string;
  clusterId: string;
  x: number;
  y: number;
  z: number;
  count: number;
  theta: TaxonomyTheta;
}

export interface ClusterSummary {
  id: string;
  label: string;
  parent: string;
  count: number;
  color: string;
}

export interface TaxonomyEdge {
  sourceId: string;
  targetId: string;
  similarity: number;
}

export type TaxonomyEdgeBundle = Record<string, TaxonomyEdge[]>;
