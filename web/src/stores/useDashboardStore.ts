"use client";

import { create } from "zustand";
import type { StageId } from "@/lib/constants/stages";
import type { AttentionEdge, GraphViewMode } from "@/types/graph";
import type { ProjectionMode, TaxonomyTheta } from "@/types/taxonomy";

interface StaticDashboardState {
  activeStage: StageId;
  taxonomy: {
    theta: TaxonomyTheta;
    selectedClusterId: string | null;
    hoveredPointId: string | null;
    projectionMode: ProjectionMode;
  };
  graph: {
    selectedFirmId: string | null;
    comparisonFirmId: string | null;
    egoTargetFirmId: string | null;
    viewMode: GraphViewMode;
    minAttentionThreshold: number;
    hoveredEdge: AttentionEdge | null;
  };
  setActiveStage: (stage: StageId) => void;
  setTheta: (theta: TaxonomyTheta) => void;
  setSelectedClusterId: (clusterId: string | null) => void;
  setHoveredPointId: (pointId: string | null) => void;
  setProjectionMode: (mode: ProjectionMode) => void;
  setSelectedFirmId: (firmId: string | null) => void;
  setComparisonFirmId: (firmId: string | null) => void;
  setEgoTargetFirmId: (firmId: string | null) => void;
  setGraphViewMode: (mode: GraphViewMode) => void;
  setMinAttentionThreshold: (threshold: number) => void;
  setHoveredEdge: (edge: AttentionEdge | null) => void;
}

export const useDashboardStore = create<StaticDashboardState>((set) => ({
  activeStage: "data-pipeline",
  taxonomy: {
    theta: 0.45,
    selectedClusterId: null,
    hoveredPointId: null,
    projectionMode: "2d"
  },
  graph: {
    selectedFirmId: "aapl",
    comparisonFirmId: null,
    egoTargetFirmId: "nvda",
    viewMode: "matrix",
    minAttentionThreshold: 0.1,
    hoveredEdge: null
  },
  setActiveStage: (activeStage) => set({ activeStage }),
  setTheta: (theta) =>
    set((state) => ({
      taxonomy: {
        ...state.taxonomy,
        theta
      }
    })),
  setSelectedClusterId: (selectedClusterId) =>
    set((state) => ({
      taxonomy: {
        ...state.taxonomy,
        selectedClusterId
      }
    })),
  setHoveredPointId: (hoveredPointId) =>
    set((state) => ({
      taxonomy: {
        ...state.taxonomy,
        hoveredPointId
      }
    })),
  setProjectionMode: (projectionMode) =>
    set((state) => ({
      taxonomy: {
        ...state.taxonomy,
        projectionMode
      }
    })),
  setSelectedFirmId: (selectedFirmId) =>
    set((state) => ({
      graph: {
        ...state.graph,
        selectedFirmId
      }
    })),
  setComparisonFirmId: (comparisonFirmId) =>
    set((state) => ({
      graph: {
        ...state.graph,
        comparisonFirmId
      }
    })),
  setEgoTargetFirmId: (egoTargetFirmId) =>
    set((state) => ({
      graph: {
        ...state.graph,
        egoTargetFirmId,
        hoveredEdge: null
      }
    })),
  setGraphViewMode: (viewMode) =>
    set((state) => ({
      graph: {
        ...state.graph,
        viewMode
      }
    })),
  setMinAttentionThreshold: (minAttentionThreshold) =>
    set((state) => ({
      graph: {
        ...state.graph,
        minAttentionThreshold
      }
    })),
  setHoveredEdge: (hoveredEdge) =>
    set((state) => ({
      graph: {
        ...state.graph,
        hoveredEdge
      }
    }))
}));
