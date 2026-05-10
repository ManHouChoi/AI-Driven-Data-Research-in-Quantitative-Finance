import { clusterPalette } from "./colors";
import type { ClusterSummary, TaxonomyEdge, UMAPPoint } from "@/types/taxonomy";

export const clusterSummaries: ClusterSummary[] = [
  {
    id: "accounting",
    label: "Accounting & Controls",
    parent: "Disclosure integrity",
    count: 1013,
    color: clusterPalette[0]
  },
  {
    id: "governance",
    label: "Governance Structure",
    parent: "Board and charter risk",
    count: 1267,
    color: clusterPalette[1]
  },
  {
    id: "debt",
    label: "Debt & Covenants",
    parent: "Financing constraints",
    count: 575,
    color: clusterPalette[2]
  },
  {
    id: "healthcare",
    label: "Healthcare Regulation",
    parent: "Policy and reimbursement",
    count: 460,
    color: clusterPalette[3]
  },
  {
    id: "operations",
    label: "Operating Fragility",
    parent: "Supply and production",
    count: 884,
    color: clusterPalette[4]
  },
  {
    id: "market",
    label: "Market Exposure",
    parent: "Demand and macro shocks",
    count: 931,
    color: clusterPalette[5]
  }
];

export const clusterColorById = Object.fromEntries(
  clusterSummaries.map((cluster) => [cluster.id, cluster.color])
);

export const macroClusterSummaries: ClusterSummary[] = [
  {
    id: "macro-operational",
    label: "Operational & External Event Risk",
    parent: "Macro risk family",
    count: 2148,
    color: clusterPalette[0]
  },
  {
    id: "macro-demand",
    label: "Demand & Macro Shocks",
    parent: "Macro risk family",
    count: 1884,
    color: clusterPalette[1]
  },
  {
    id: "macro-financing",
    label: "Financing Constraints",
    parent: "Macro risk family",
    count: 1519,
    color: clusterPalette[2]
  },
  {
    id: "macro-policy",
    label: "Policy & Legal Exposure",
    parent: "Macro risk family",
    count: 1392,
    color: clusterPalette[3]
  },
  {
    id: "macro-governance",
    label: "Governance & Disclosure Risk",
    parent: "Macro risk family",
    count: 1276,
    color: clusterPalette[4]
  },
  {
    id: "macro-technology",
    label: "Technology & Cyber Continuity",
    parent: "Macro risk family",
    count: 1107,
    color: clusterPalette[5]
  },
  {
    id: "macro-supply",
    label: "Supply Chain & Production Risk",
    parent: "Macro risk family",
    count: 1634,
    color: clusterPalette[0]
  },
  {
    id: "macro-competition",
    label: "Market Structure & Competition",
    parent: "Macro risk family",
    count: 1219,
    color: clusterPalette[1]
  }
];

export const macroClusterColorById = Object.fromEntries(
  macroClusterSummaries.map((cluster) => [cluster.id, cluster.color])
);

export const macroTopologyPoints: UMAPPoint[] = [
  {
    id: "macro-operational",
    label: "Operational & External Event Risk",
    parent: "Macro risk family",
    clusterId: "macro-operational",
    x: -2.4,
    y: 0.6,
    z: 0.8,
    count: 2148,
    theta: 0.45
  },
  {
    id: "macro-demand",
    label: "Demand & Macro Shocks",
    parent: "Macro risk family",
    clusterId: "macro-demand",
    x: -1.2,
    y: -1.4,
    z: 0.1,
    count: 1884,
    theta: 0.45
  },
  {
    id: "macro-financing",
    label: "Financing Constraints",
    parent: "Macro risk family",
    clusterId: "macro-financing",
    x: 0.7,
    y: -1.7,
    z: -0.5,
    count: 1519,
    theta: 0.45
  },
  {
    id: "macro-policy",
    label: "Policy & Legal Exposure",
    parent: "Macro risk family",
    clusterId: "macro-policy",
    x: 2.3,
    y: -0.2,
    z: 0.5,
    count: 1392,
    theta: 0.45
  },
  {
    id: "macro-governance",
    label: "Governance & Disclosure Risk",
    parent: "Macro risk family",
    clusterId: "macro-governance",
    x: 1.2,
    y: 1.7,
    z: 0.9,
    count: 1276,
    theta: 0.45
  },
  {
    id: "macro-technology",
    label: "Technology & Cyber Continuity",
    parent: "Macro risk family",
    clusterId: "macro-technology",
    x: -0.6,
    y: 2.0,
    z: -0.7,
    count: 1107,
    theta: 0.45
  },
  {
    id: "macro-supply",
    label: "Supply Chain & Production Risk",
    parent: "Macro risk family",
    clusterId: "macro-supply",
    x: -2.0,
    y: 1.8,
    z: -0.1,
    count: 1634,
    theta: 0.45
  },
  {
    id: "macro-competition",
    label: "Market Structure & Competition",
    parent: "Macro risk family",
    clusterId: "macro-competition",
    x: 2.0,
    y: 1.0,
    z: -0.2,
    count: 1219,
    theta: 0.45
  }
];

export const macroTopologyEdges: TaxonomyEdge[] = [
  { sourceId: "macro-operational", targetId: "macro-demand", similarity: 0.91 },
  { sourceId: "macro-operational", targetId: "macro-financing", similarity: 0.82 },
  { sourceId: "macro-operational", targetId: "macro-policy", similarity: 0.88 },
  { sourceId: "macro-operational", targetId: "macro-governance", similarity: 0.79 },
  { sourceId: "macro-operational", targetId: "macro-technology", similarity: 0.84 },
  { sourceId: "macro-operational", targetId: "macro-supply", similarity: 0.93 },
  { sourceId: "macro-operational", targetId: "macro-competition", similarity: 0.86 },
  { sourceId: "macro-demand", targetId: "macro-financing", similarity: 0.87 },
  { sourceId: "macro-demand", targetId: "macro-policy", similarity: 0.8 },
  { sourceId: "macro-demand", targetId: "macro-supply", similarity: 0.84 },
  { sourceId: "macro-demand", targetId: "macro-competition", similarity: 0.92 },
  { sourceId: "macro-financing", targetId: "macro-policy", similarity: 0.78 },
  { sourceId: "macro-financing", targetId: "macro-governance", similarity: 0.83 },
  { sourceId: "macro-financing", targetId: "macro-competition", similarity: 0.76 },
  { sourceId: "macro-policy", targetId: "macro-governance", similarity: 0.86 },
  { sourceId: "macro-policy", targetId: "macro-technology", similarity: 0.75 },
  { sourceId: "macro-policy", targetId: "macro-supply", similarity: 0.81 },
  { sourceId: "macro-policy", targetId: "macro-competition", similarity: 0.89 },
  { sourceId: "macro-governance", targetId: "macro-technology", similarity: 0.78 },
  { sourceId: "macro-governance", targetId: "macro-competition", similarity: 0.74 },
  { sourceId: "macro-technology", targetId: "macro-supply", similarity: 0.82 },
  { sourceId: "macro-technology", targetId: "macro-competition", similarity: 0.77 },
  { sourceId: "macro-supply", targetId: "macro-competition", similarity: 0.88 }
];
