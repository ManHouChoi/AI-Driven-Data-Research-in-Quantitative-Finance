import type { AttentionMatrixData } from "./graph";
import type { PortfolioReturnPoint } from "./portfolio";
import type { TaxonomyTheta, UMAPPoint } from "./taxonomy";

export interface StaticDataBundle {
  umap: Record<TaxonomyTheta, UMAPPoint[]>;
  attention: AttentionMatrixData;
  portfolio: PortfolioReturnPoint[];
}
