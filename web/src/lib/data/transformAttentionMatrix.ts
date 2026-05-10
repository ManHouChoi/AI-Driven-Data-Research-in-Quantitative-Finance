import type { TaxonomyTheta } from "@/types/taxonomy";

export function transformAttentionMatrixForTheta(
  matrix: number[][],
  theta: TaxonomyTheta
) {
  const sensitivityLift = theta === 0.4 ? 0.045 : 0;
  const crossSectorPenalty = theta === 0.4 ? 0.012 : 0;

  return matrix.map((row, sourceIndex) =>
    row.map((alpha, targetIndex) => {
      if (sourceIndex === targetIndex) {
        return 0;
      }

      const localNeighborhood = Math.abs(sourceIndex - targetIndex) <= 1;
      const adjusted =
        alpha +
        sensitivityLift * (localNeighborhood ? 1.15 : 0.72) -
        crossSectorPenalty * (localNeighborhood ? 0 : 1);

      return Number(Math.max(0, Math.min(0.94, adjusted)).toFixed(3));
    })
  );
}
