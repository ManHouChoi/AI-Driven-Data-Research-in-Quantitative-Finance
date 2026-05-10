"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import "echarts-gl";
import { Info } from "lucide-react";
import { MathText } from "@/components/ui/MathText";
import { useUMAPData } from "@/lib/data/loadUMAPData";
import { chartColors } from "@/lib/constants/colors";
import { clusterColorById, clusterSummaries } from "@/lib/constants/taxonomy";
import { useDashboardStore } from "@/stores/useDashboardStore";

export function UMAPScatterPlot() {
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const projectionMode = useDashboardStore(
    (state) => state.taxonomy.projectionMode
  );
  const selectedClusterId = useDashboardStore(
    (state) => state.taxonomy.selectedClusterId
  );
  const setHoveredPointId = useDashboardStore(
    (state) => state.setHoveredPointId
  );
  const { points, edges, isLoading } = useUMAPData(theta);

  const filteredPoints = selectedClusterId
    ? points.filter((point) => point.clusterId === selectedClusterId)
    : points;

  const grouped = clusterSummaries.map((cluster) => ({
    cluster,
    points: filteredPoints.filter((point) => point.clusterId === cluster.id)
  }));

  const option = useMemo(() => {
    const pointById = new Map(filteredPoints.map((point) => [point.id, point]));
    const visibleEdges = edges
      .filter(
        (edge) =>
          edge.similarity >= theta &&
          pointById.has(edge.sourceId) &&
          pointById.has(edge.targetId)
      )
      .slice(0, projectionMode === "3d" ? 44 : 64);

    const baseTooltip = {
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

    const scatterSeries = grouped.map(({ cluster, points: clusterPoints }) => ({
      name: cluster.label,
      type: projectionMode === "3d" ? "scatter3D" : "scatter",
      coordinateSystem:
        projectionMode === "3d" ? "cartesian3D" : "cartesian2d",
      dimensions:
        projectionMode === "3d"
          ? ["x", "y", "z", "label", "id", "parent", "count"]
          : undefined,
      symbolSize:
        projectionMode === "3d"
          ? 12
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
              return Math.max(10, Math.min(36, Math.sqrt(count) * 1.35));
            },
      itemStyle: {
        color: clusterColorById[cluster.id],
        opacity: selectedClusterId ? 0.94 : 0.8
      },
      emphasis: {
        focus: "series"
      },
      animationDurationUpdate: 320,
      data: clusterPoints.map((point) => [
        point.x,
        point.y,
        point.z,
        point.label,
        point.id,
        point.parent,
        point.count
      ])
    }));

    if (projectionMode === "3d") {
      return {
        backgroundColor: "transparent",
        tooltip: baseTooltip,
        grid3D: {
          axisLine: { lineStyle: { color: "#d6d6dc" } },
          axisPointer: { lineStyle: { color: chartColors.mercuryBlue } },
          splitLine: { lineStyle: { color: "rgba(210,210,215,0.5)" } },
          viewControl: {
            alpha: 24,
            beta: 42,
            distance: 150,
            autoRotate: true,
            autoRotateAfterStill: 3,
            autoRotateSpeed: 2,
            rotateSensitivity: 1,
            zoomSensitivity: 1,
            panSensitivity: 1
          },
          boxWidth: 120,
          boxHeight: 70,
          boxDepth: 90,
          environment: "#ffffff"
        },
        xAxis3D: { type: "value", name: "UMAP-1", nameTextStyle: { color: chartColors.ink } },
        yAxis3D: { type: "value", name: "UMAP-2", nameTextStyle: { color: chartColors.ink } },
        zAxis3D: { type: "value", name: "UMAP-3", nameTextStyle: { color: chartColors.ink } },
        series: [
          ...visibleEdges.map((edge, index) => {
            const source = pointById.get(edge.sourceId)!;
            const target = pointById.get(edge.targetId)!;

            return {
              name: `A risk edge ${index + 1}`,
              type: "line3D",
              coordinateSystem: "cartesian3D",
              dimensions: ["x", "y", "z"],
              silent: true,
              lineStyle: {
                color: "rgba(82,102,235,0.28)",
                width: 1
              },
              data: [
                [source.x, source.y, source.z],
                [target.x, target.y, target.z]
              ]
            };
          }),
          ...scatterSeries
        ],
        animationDurationUpdate: 320
      };
    }

    return {
      backgroundColor: "transparent",
      tooltip: baseTooltip,
      grid: {
        left: 48,
        right: 24,
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
          name: "A risk edges",
          type: "lines",
          silent: true,
          coordinateSystem: "cartesian2d",
          lineStyle: {
            color: "rgba(82,102,235,0.24)",
            width: 1,
            opacity: 0.8
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
      ]
    };
  }, [edges, filteredPoints, grouped, projectionMode, selectedClusterId, theta]);

  return (
    <div className="relative">
      <div className="group absolute right-3 top-3 z-10">
        <button
          aria-label="Taxonomy edge definition"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-white/90 text-apple-ink ring-1 ring-apple-mist"
          type="button"
        >
          <Info className="h-4 w-4" />
        </button>
        <div className="pointer-events-none absolute right-0 top-11 hidden w-80 rounded-lg bg-apple-ink p-3 text-xs leading-5 text-white group-hover:block">
          Edges represent <MathText math="A_{i,j}^{risk}=1" />, where cosine
          similarity between risk exposure vectors exceeds the threshold{" "}
          <MathText math="\tau" />.
        </div>
      </div>
      {isLoading ? (
        <div className="flex h-[460px] items-center justify-center text-sm text-apple-graphite">
          Loading taxonomy graph...
        </div>
      ) : (
        <ReactECharts
          className={projectionMode === "3d" ? "h-[540px] w-full" : "h-[460px] w-full"}
          key={`${projectionMode}-${theta}-${selectedClusterId ?? "all"}`}
          lazyUpdate={false}
          notMerge
          option={option}
          opts={{ renderer: "canvas" }}
          style={{
            height: projectionMode === "3d" ? 540 : 460,
            width: "100%"
          }}
          onEvents={{
            mouseover: (params: { data?: unknown[] }) => {
              const data = params.data as unknown[] | undefined;
              setHoveredPointId(typeof data?.[4] === "string" ? data[4] : null);
            },
            mouseout: () => setHoveredPointId(null)
          }}
        />
      )}
    </div>
  );
}
