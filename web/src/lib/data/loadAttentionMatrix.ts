"use client";

import { useEffect, useState } from "react";
import type { AttentionMatrixData } from "@/types/graph";

export function useAttentionMatrix() {
  const [data, setData] = useState<AttentionMatrixData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetch("/data/attention_matrix.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load attention matrix");
        }
        return response.json() as Promise<AttentionMatrixData>;
      })
      .then((nextData) => {
        if (!cancelled) {
          setData(nextData);
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { data, isLoading };
}
