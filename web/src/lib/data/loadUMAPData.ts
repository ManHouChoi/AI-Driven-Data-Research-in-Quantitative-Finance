"use client";

import { useEffect, useState } from "react";
import type {
  TaxonomyEdge,
  TaxonomyEdgeBundle,
  TaxonomyTheta,
  UMAPPoint
} from "@/types/taxonomy";

const thetaFileByValue: Record<TaxonomyTheta, string> = {
  0.45: "umap_theta_045.json",
  0.4: "umap_theta_040.json"
};

export function useUMAPData(theta: TaxonomyTheta) {
  const [points, setPoints] = useState<UMAPPoint[]>([]);
  const [edges, setEdges] = useState<TaxonomyEdge[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      const [pointResponse, edgeResponse] = await Promise.all([
        fetch(`/data/${thetaFileByValue[theta]}`),
        fetch("/data/taxonomy_edges.json")
      ]);

      if (!pointResponse.ok || !edgeResponse.ok) {
        throw new Error("Failed to load taxonomy data");
      }

      const [nextPoints, edgeBundle] = (await Promise.all([
        pointResponse.json(),
        edgeResponse.json()
      ])) as [UMAPPoint[], TaxonomyEdgeBundle];

      if (!cancelled) {
        setPoints(nextPoints);
        setEdges(edgeBundle[String(theta)] ?? []);
        setIsLoading(false);
      }
    }

    load().catch(() => {
      if (!cancelled) {
        setPoints([]);
        setEdges([]);
        setIsLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [theta]);

  return { points, edges, isLoading };
}
