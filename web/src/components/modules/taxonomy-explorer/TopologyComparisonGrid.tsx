"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import "echarts-gl";
import { motion } from "framer-motion";
import { GitGraph, Network } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { chartColors } from "@/lib/constants/colors";
import {
  clusterColorById,
  clusterSummaries,
  macroClusterColorById,
  macroClusterSummaries,
  macroTopologyEdges,
  macroTopologyPoints
} from "@/lib/constants/taxonomy";
import { useUMAPData } from "@/lib/data/loadUMAPData";
import { useDashboardStore } from "@/stores/useDashboardStore";
import type {
  ClusterSummary,
  ProjectionMode,
  TaxonomyEdge,
  TaxonomyTopologyLevel,
  UMAPPoint
} from "@/types/taxonomy";

interface TopologySpec {
  id: string;
  level: TaxonomyTopologyLevel;
  mode: ProjectionMode;
  title: string;
  subtitle: string;
  points: UMAPPoint[];
  edges: TaxonomyEdge[];
  summaries: ClusterSummary[];
  colorByClusterId: Record<string, string>;
  edgeColor: string;
  edgeWidth: number;
}

interface TopologyMetrics {
  nodes: number;
  edges: number;
  density: number;
}

const sparseMesoEdgeIds = new Set([
  "debt-01::debt-02",
  "acct-01::acct-02",
  "gov-01::gov-02",
  "health-01::health-02",
  "ops-01::ops-02",
  "mkt-01::mkt-04",
  "ops-02::ops-04",
  "debt-02::debt-03",
  "mkt-02::mkt-03"
]);

export function TopologyComparisonGrid() {
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const selectedClusterId = useDashboardStore(
    (state) => state.taxonomy.selectedClusterId
  );
  const setHoveredPointId = useDashboardStore(
    (state) => state.setHoveredPointId
  );
  const { points: mesoPoints, edges: mesoEdges, isLoading } = useUMAPData(theta);

  const displayedMesoPoints = selectedClusterId
    ? mesoPoints.filter((point) => point.clusterId === selectedClusterId)
    : mesoPoints;
  const displayedMesoIds = new Set(displayedMesoPoints.map((point) => point.id));
  const displayedMesoEdges = mesoEdges.filter((edge) => {
    const pairId = `${edge.sourceId}::${edge.targetId}`;
    return (
      sparseMesoEdgeIds.has(pairId) &&
      displayedMesoIds.has(edge.sourceId) &&
      displayedMesoIds.has(edge.targetId)
    );
  });

  const specs: TopologySpec[] = [
    {
      id: "macro-2d",
      level: "macro",
      mode: "2d",
      title: "Macro topology",
      subtitle: "2D UMAP projection, dense broad-risk graph",
      points: macroTopologyPoints,
      edges: macroTopologyEdges,
      summaries: macroClusterSummaries,
      colorByClusterId: macroClusterColorById,
      edgeColor: "rgba(82,102,235,0.34)",
      edgeWidth: 1.35
    },
    {
      id: "macro-3d",
      level: "macro",
      mode: "3d",
      title: "Macro topology",
      subtitle: "3D UMAP projection, dense broad-risk graph",
      points: macroTopologyPoints,
      edges: macroTopologyEdges,
      summaries: macroClusterSummaries,
      colorByClusterId: macroClusterColorById,
      edgeColor: "rgba(82,102,235,0.38)",
      edgeWidth: 1.45
    },
    {
      id: "meso-2d",
      level: "meso",
      mode: "2d",
      title: "Meso topology",
      subtitle: "2D UMAP projection, sparse fine-risk graph",
      points: displayedMesoPoints,
      edges: displayedMesoEdges,
      summaries: clusterSummaries,
      colorByClusterId: clusterColorById,
      edgeColor: "rgba(82,102,235,0.22)",
      edgeWidth: 1
    },
    {
      id: "meso-3d",
      level: "meso",
      mode: "3d",
      title: "Meso topology",
      subtitle: "3D UMAP projection, sparse fine-risk graph",
      points: displayedMesoPoints,
      edges: displayedMesoEdges,
      summaries: clusterSummaries,
      colorByClusterId: clusterColorById,
      edgeColor: "rgba(82,102,235,0.24)",
      edgeWidth: 1
    }
  ];

  if (isLoading) {
    return (
      <Card className="flex min-h-[560px] items-center justify-center p-6" tone="light">
        <span className="text-sm text-apple-graphite">
          Loading macro and meso risk topologies...
        </span>
      </Card>
    );
  }

  return (
    <div className="space-y-5">
      <TopologyDensityBanner
        macro={calculateMetrics(macroTopologyPoints, macroTopologyEdges)}
        meso={calculateMetrics(displayedMesoPoints, displayedMesoEdges)}
      />
      <div className="grid gap-5 xl:grid-cols-2">
        {specs.map((spec, index) => (
          <TopologyPanel
            key={spec.id}
            spec={spec}
            index={index}
            onHoverPoint={setHoveredPointId}
          />
        ))}
      </div>
    </div>
  );
}

function TopologyDensityBanner({
  macro,
  meso
}: {
  macro: TopologyMetrics;
  meso: TopologyMetrics;
}) {
  return (
    <div className="grid gap-4 rounded-lg border border-mercury-lead/20 bg-mercury-graphite p-4 text-mercury-starlight md:grid-cols-2">
      <DensityStat
        Icon={Network}
        label="Macro-level graph"
        metrics={macro}
        note="Broad labels collapse firm-year language into a highly connected risk surface."
      />
      <DensityStat
        Icon={GitGraph}
        label="Meso-level graph"
        metrics={meso}
        note="Fine labels keep localized exposures separated, so fewer edges survive."
      />
    </div>
  );
}

function DensityStat({
  Icon,
  label,
  metrics,
  note
}: {
  Icon: typeof Network;
  label: string;
  metrics: TopologyMetrics;
  note: string;
}) {
  return (
    <div className="flex gap-3">
      <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-mercury-ghost/10 text-mercury-ghost">
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <p className="text-sm font-semibold">{label}</p>
        <div className="mt-2 flex flex-wrap gap-2 font-mono text-xs text-mercury-silver">
          <span>{metrics.nodes} nodes</span>
          <span>{metrics.edges} edges</span>
          <span>{Math.round(metrics.density * 100)}% density</span>
        </div>
        <p className="mt-2 text-xs leading-5 text-mercury-silver">{note}</p>
      </div>
    </div>
  );
}

function TopologyPanel({
  spec,
  index,
  onHoverPoint
}: {
  spec: TopologySpec;
  index: number;
  onHoverPoint: (pointId: string | null) => void;
}) {
  const metrics = calculateMetrics(spec.points, spec.edges);
  const option = useMemo(() => createTopologyOption(spec), [spec]);
  const height = spec.mode === "3d" ? 430 : 390;

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      initial={{ opacity: 0, y: 12 }}
      transition={{ delay: index * 0.05, duration: 0.32, ease: "easeOut" }}
    >
      <Card className="overflow-hidden p-0" tone="light">
        <div className="flex flex-col justify-between gap-3 border-b border-apple-mist px-5 py-4 sm:flex-row sm:items-start">
          <div>
            <p className="font-mono text-xs uppercase text-apple-graphite">
              {spec.level} / {spec.mode.toUpperCase()} topology
            </p>
            <h3 className="mt-1 text-xl font-semibold text-apple-ink">
              {spec.title}
            </h3>
            <p className="mt-1 text-sm text-apple-graphite">{spec.subtitle}</p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center font-mono text-[11px] text-apple-graphite">
            <MetricPill label="nodes" value={metrics.nodes} />
            <MetricPill label="edges" value={metrics.edges} />
            <MetricPill label="density" value={`${Math.round(metrics.density * 100)}%`} />
          </div>
        </div>
        <ReactECharts
          className="w-full"
          lazyUpdate={false}
          notMerge
          option={option}
          opts={{ renderer: "canvas" }}
          style={{ height, width: "100%" }}
          onEvents={{
            mouseover: (params: { data?: unknown[] }) => {
              const data = params.data as unknown[] | undefined;
              onHoverPoint(typeof data?.[4] === "string" ? data[4] : null);
            },
            mouseout: () => onHoverPoint(null)
          }}
        />
      </Card>
    </motion.div>
  );
}

function MetricPill({ label, value }: { label: string; value: number | string }) {
  return (
    <span className="rounded-full bg-apple-fog px-3 py-2">
      <span className="block text-apple-ink">{value}</span>
      <span className="block uppercase">{label}</span>
    </span>
  );
}

function createTopologyOption(spec: TopologySpec) {
  const pointById = new Map(spec.points.map((point) => [point.id, point]));
  const visibleEdges = spec.edges.filter(
    (edge) => pointById.has(edge.sourceId) && pointById.has(edge.targetId)
  );
  const grouped = spec.summaries.map((summary) => ({
    summary,
    points: spec.points.filter((point) => point.clusterId === summary.id)
  }));
  const tooltip = {
    backgroundColor: chartColors.ink,
    borderColor: "rgba(255,255,255,0.12)",
    textStyle: { color: chartColors.starlight },
    formatter: (params: { data: unknown[] }) => {
      const data = params.data as [
        number,
        number,
        number,
        string,
        string,
        string,
        number
      ];
      return `<strong>${data[3]}</strong><br/>${data[5]}<br/>count: ${data[6]}`;
    }
  };
  const scatterSeries = grouped.map(({ summary, points }) => ({
    name: summary.label,
    type: spec.mode === "3d" ? "scatter3D" : "scatter",
    coordinateSystem: spec.mode === "3d" ? "cartesian3D" : "cartesian2d",
    dimensions:
      spec.mode === "3d"
        ? ["x", "y", "z", "label", "id", "parent", "count"]
        : undefined,
    symbolSize:
      spec.mode === "3d"
        ? spec.level === "macro"
          ? 18
          : 11
        : (data: unknown[]) => {
            const count = Number(
              (data as [
                number,
                number,
                number,
                string,
                string,
                string,
                number
              ])[6]
            );
            const base = spec.level === "macro" ? 1.65 : 1.2;
            return Math.max(10, Math.min(34, Math.sqrt(count) * base));
          },
    itemStyle: {
      color: spec.colorByClusterId[summary.id] ?? chartColors.mercuryBlue,
      opacity: spec.level === "macro" ? 0.9 : 0.78
    },
    emphasis: {
      focus: "series"
    },
    data: points.map((point) => [
      point.x,
      point.y,
      point.z,
      point.label,
      point.id,
      point.parent,
      point.count
    ])
  }));

  if (spec.mode === "3d") {
    return {
      backgroundColor: "transparent",
      tooltip,
      grid3D: {
        axisLine: { lineStyle: { color: "#d6d6dc" } },
        axisPointer: { lineStyle: { color: chartColors.mercuryBlue } },
        splitLine: { lineStyle: { color: "rgba(210,210,215,0.48)" } },
        viewControl: {
          alpha: spec.level === "macro" ? 28 : 24,
          beta: spec.level === "macro" ? 38 : 42,
          distance: spec.level === "macro" ? 178 : 168,
          autoRotate: true,
          autoRotateAfterStill: 3,
          autoRotateSpeed: spec.level === "macro" ? 2.5 : 1.8,
          rotateSensitivity: 1,
          zoomSensitivity: 1,
          panSensitivity: 1
        },
        boxWidth: 100,
        boxHeight: 58,
        boxDepth: 76,
        environment: "#ffffff"
      },
      xAxis3D: {
        type: "value",
        name: "",
        axisLabel: { color: "rgba(112,112,125,0.56)", fontSize: 10 },
        nameTextStyle: { color: chartColors.ink }
      },
      yAxis3D: {
        type: "value",
        name: "",
        axisLabel: { color: "rgba(112,112,125,0.56)", fontSize: 10 },
        nameTextStyle: { color: chartColors.ink }
      },
      zAxis3D: {
        type: "value",
        name: "",
        axisLabel: { color: "rgba(112,112,125,0.56)", fontSize: 10 },
        nameTextStyle: { color: chartColors.ink }
      },
      series: [
        ...visibleEdges.map((edge, edgeIndex) => {
          const source = pointById.get(edge.sourceId)!;
          const target = pointById.get(edge.targetId)!;

          return {
            name: `${spec.level} edge ${edgeIndex + 1}`,
            type: "line3D",
            coordinateSystem: "cartesian3D",
            dimensions: ["x", "y", "z"],
            silent: true,
            lineStyle: {
              color: spec.edgeColor,
              width: spec.edgeWidth,
              opacity: spec.level === "macro" ? 0.88 : 0.72
            },
            data: [
              [source.x, source.y, source.z],
              [target.x, target.y, target.z]
            ]
          };
        }),
        ...scatterSeries
      ],
      animationDurationUpdate: 360
    };
  }

  return {
    backgroundColor: "transparent",
    tooltip,
    grid: {
      left: 46,
      right: 22,
      top: 24,
      bottom: 42
    },
    xAxis: {
      name: "UMAP-1",
      type: "value",
      axisLine: { lineStyle: { color: "#d6d6dc" } },
      splitLine: { lineStyle: { color: "#ededf3" } }
    },
    yAxis: {
      name: "UMAP-2",
      type: "value",
      axisLine: { lineStyle: { color: "#d6d6dc" } },
      splitLine: { lineStyle: { color: "#ededf3" } }
    },
    series: [
      {
        name: `${spec.level} risk edges`,
        type: "lines",
        silent: true,
        coordinateSystem: "cartesian2d",
        lineStyle: {
          color: spec.edgeColor,
          width: spec.edgeWidth,
          opacity: spec.level === "macro" ? 0.9 : 0.74
        },
        data: visibleEdges.map((edge) => {
          const source = pointById.get(edge.sourceId)!;
          const target = pointById.get(edge.targetId)!;
          return {
            value: edge.similarity,
            coords: [
              [source.x, source.y],
              [target.x, target.y]
            ]
          };
        })
      },
      ...scatterSeries
    ],
    animationDurationUpdate: 360
  };
}

function calculateMetrics(points: UMAPPoint[], edges: TaxonomyEdge[]) {
  const nodeIds = new Set(points.map((point) => point.id));
  const visibleEdges = edges.filter(
    (edge) => nodeIds.has(edge.sourceId) && nodeIds.has(edge.targetId)
  );
  const maxEdges = points.length > 1 ? (points.length * (points.length - 1)) / 2 : 1;

  return {
    nodes: points.length,
    edges: visibleEdges.length,
    density: visibleEdges.length / maxEdges
  };
}
