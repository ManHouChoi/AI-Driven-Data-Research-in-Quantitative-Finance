"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import katex from "katex";
import { MathText } from "@/components/ui/MathText";
import { useAttentionMatrix } from "@/lib/data/loadAttentionMatrix";
import { transformAttentionMatrixForTheta } from "@/lib/data/transformAttentionMatrix";
import { chartColors } from "@/lib/constants/colors";
import { useDashboardStore } from "@/stores/useDashboardStore";

export function AttentionHeatmap() {
  const { data: attentionData, isLoading } = useAttentionMatrix();
  const firms = attentionData?.firms ?? [];
  const baseMatrix = attentionData?.matrix ?? [];
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const matrix = useMemo(
    () => transformAttentionMatrixForTheta(baseMatrix, theta),
    [baseMatrix, theta]
  );
  const threshold = useDashboardStore(
    (state) => state.graph.minAttentionThreshold
  );
  const selectedFirmId = useDashboardStore((state) => state.graph.selectedFirmId);
  const comparisonFirmId = useDashboardStore(
    (state) => state.graph.comparisonFirmId
  );
  const setHoveredEdge = useDashboardStore((state) => state.setHoveredEdge);

  const labels = firms.map((firm) => firm.ticker);
  const selectedIndex = firms.findIndex((firm) => firm.id === selectedFirmId);
  const comparisonIndex = firms.findIndex((firm) => firm.id === comparisonFirmId);

  const data = useMemo(
    () =>
      matrix.flatMap((row, y) =>
        row.map((alpha, x) => [
          x,
          y,
          alpha >= threshold ? alpha : 0,
          firms[y].id,
          firms[x].id,
          firms[y].ticker,
          firms[x].ticker,
          alpha
        ])
      ),
    [firms, matrix, threshold]
  );

  const option = useMemo(
    () => ({
      backgroundColor: "transparent",
      tooltip: {
        backgroundColor: chartColors.ink,
        borderColor: "rgba(255,255,255,0.12)",
        textStyle: { color: chartColors.starlight },
        formatter: (params: { data: unknown[] }) => {
          const value = params.data as [
            number,
            number,
            number,
            string,
            string,
            string,
            string,
            number
          ];
          const alphaLabel = katex.renderToString("\\alpha_{ij}", {
            throwOnError: false
          });
          return `<strong>${value[5]} &rarr; ${value[6]}</strong><br/>${alphaLabel}: ${value[7].toFixed(3)}`;
        }
      },
      grid: {
        left: 66,
        right: 26,
        top: 32,
        bottom: 58
      },
      xAxis: {
        type: "category",
        data: labels,
        axisLabel: { color: chartColors.ink, rotate: 35 },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "#d6d6dc" } }
      },
      yAxis: {
        type: "category",
        data: labels,
        axisLabel: { color: chartColors.ink },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "#d6d6dc" } }
      },
      visualMap: {
        min: 0,
        max: 0.9,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 4,
        textStyle: { color: chartColors.ink },
        inRange: {
          color: ["#f5f5f7", "#cdddff", "#5266eb", "#1d1d1f"]
        }
      },
      series: [
        {
          type: "heatmap",
          data,
          label: {
            show: true,
            formatter: (params: { data: unknown[] }) => {
              const value = (params.data as unknown[])[7];
              return typeof value === "number" && value >= threshold
                ? value.toFixed(2)
                : "";
            },
            color: chartColors.ink,
            fontSize: 10
          },
          itemStyle: {
            borderColor: "#ffffff",
            borderWidth: 2
          },
          emphasis: {
            itemStyle: {
              borderColor: chartColors.ink,
              borderWidth: 2
            }
          },
          markLine: {
            silent: true,
            symbol: "none",
            data: [
              selectedIndex >= 0
                ? { yAxis: selectedIndex, lineStyle: { color: "#5266eb", width: 2 } }
                : null,
              comparisonIndex >= 0
                ? { xAxis: comparisonIndex, lineStyle: { color: "#2aa889", width: 2 } }
                : null
            ].filter(Boolean)
          }
        }
      ]
    }),
    [comparisonIndex, data, labels, selectedIndex, threshold]
  );

  return (
    <>
      {isLoading ? (
        <div className="flex h-[500px] items-center justify-center text-sm text-apple-graphite">
          Loading attention matrix...
        </div>
      ) : (
        <div>
          <div className="flex items-center justify-between px-3 pt-2 text-xs text-apple-graphite">
            <span>Matrix data conditioned on taxonomy sensitivity</span>
            <span className="font-mono">
              <MathText math={`\\theta=${theta.toFixed(2)}`} />
            </span>
          </div>
          <ReactECharts
            className="h-[500px] w-full"
            option={option}
            opts={{ renderer: "canvas" }}
            onEvents={{
            mouseover: (params: { data?: unknown[] }) => {
              const value = params.data as unknown[] | undefined;
              if (!value || typeof value[7] !== "number") {
                return;
              }
              setHoveredEdge({
                sourceFirmId: String(value[3]),
                targetFirmId: String(value[4]),
                alpha: Number(value[7])
              });
            },
            mouseout: () => setHoveredEdge(null)
            }}
          />
        </div>
      )}
    </>
  );
}
