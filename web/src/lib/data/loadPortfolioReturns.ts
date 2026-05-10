"use client";

import { useEffect, useState } from "react";
import type { CaseStudyData, PortfolioReturnPoint } from "@/types/portfolio";

export function usePortfolioReturns() {
  const [data, setData] = useState<PortfolioReturnPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetch("/data/portfolio_returns.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load portfolio returns");
        }
        return response.json() as Promise<PortfolioReturnPoint[]>;
      })
      .then((nextData) => {
        if (!cancelled) {
          setData(nextData);
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData([]);
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { data, isLoading };
}

export function useCaseStudyData() {
  const [data, setData] = useState<CaseStudyData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetch("/data/case_study.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load case study data");
        }
        return response.json() as Promise<CaseStudyData>;
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
