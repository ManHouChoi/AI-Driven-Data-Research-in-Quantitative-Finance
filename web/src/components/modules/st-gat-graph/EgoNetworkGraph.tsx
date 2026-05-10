"use client";

import { useMemo } from "react";
import { MathText } from "@/components/ui/MathText";
import { useAttentionMatrix } from "@/lib/data/loadAttentionMatrix";
import { transformAttentionMatrixForTheta } from "@/lib/data/transformAttentionMatrix";
import { chartColors } from "@/lib/constants/colors";
import { useDashboardStore } from "@/stores/useDashboardStore";

export function EgoNetworkGraph() {
  const { data, isLoading } = useAttentionMatrix();
  const theta = useDashboardStore((state) => state.taxonomy.theta);
  const egoTargetFirmId = useDashboardStore(
    (state) => state.graph.egoTargetFirmId
  );

  const firms = data?.firms ?? [];
  const matrix = useMemo(
    () => transformAttentionMatrixForTheta(data?.matrix ?? [], theta),
    [data?.matrix, theta]
  );
  const targetIndex = Math.max(
    0,
    firms.findIndex((firm) => firm.id === egoTargetFirmId)
  );
  const targetFirm = firms[targetIndex];

  const incoming = useMemo(
    () =>
      firms
        .map((firm, sourceIndex) => ({
          firm,
          alpha: matrix[sourceIndex]?.[targetIndex] ?? 0
        }))
        .filter((entry) => entry.firm.id !== targetFirm?.id)
        .sort((a, b) => b.alpha - a.alpha)
        .slice(0, 5),
    [firms, matrix, targetFirm?.id, targetIndex]
  );

  const outgoing = useMemo(
    () =>
      (matrix[targetIndex] ?? [])
        .map((alpha, firmIndex) => ({
          firm: firms[firmIndex],
          alpha
        }))
        .filter((entry) => entry.firm && entry.firm.id !== targetFirm?.id)
        .sort((a, b) => b.alpha - a.alpha)
        .slice(0, 5),
    [firms, matrix, targetFirm?.id, targetIndex]
  );

  if (isLoading || !targetFirm) {
    return (
      <div className="flex h-[540px] items-center justify-center text-sm text-apple-graphite">
        Loading ego network...
      </div>
    );
  }

  const leftNodes = layoutColumn(incoming.length, 110);
  const rightNodes = layoutColumn(outgoing.length, 850);
  const center = { x: 480, y: 270 };

  return (
    <div className="relative h-[540px] overflow-hidden rounded-lg bg-white">
      <div className="absolute left-5 top-4 z-10 text-xs text-apple-graphite">
        <span>Directed top attention neighborhoods</span>
        <span className="ml-3 font-mono">
          <MathText math={`\\theta=${theta.toFixed(2)}`} />
        </span>
      </div>
      <svg
        aria-label={`Ego network for ${targetFirm.ticker}`}
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
        viewBox="0 0 960 540"
      >
        <defs>
          <marker
            id="ego-arrow"
            markerHeight="8"
            markerWidth="8"
            orient="auto"
            refX="7"
            refY="4"
          >
            <path d="M0,0 L8,4 L0,8 Z" fill={chartColors.mercuryBlue} />
          </marker>
        </defs>

        {incoming.map((entry, index) => (
          <Edge
            alpha={entry.alpha}
            key={`in-${entry.firm.id}`}
            source={leftNodes[index]}
            target={center}
          />
        ))}
        {outgoing.map((entry, index) => (
          <Edge
            alpha={entry.alpha}
            key={`out-${entry.firm.id}`}
            source={center}
            target={rightNodes[index]}
          />
        ))}

        {incoming.map((entry, index) => (
          <FirmNode
            alpha={entry.alpha}
            key={entry.firm.id}
            label={entry.firm.ticker}
            sector={entry.firm.sector}
            x={leftNodes[index].x}
            y={leftNodes[index].y}
          />
        ))}

        <g>
          <circle cx={center.x} cy={center.y} fill="#1d1d1f" r="58" />
          <text
            fill="#ffffff"
            fontSize="24"
            fontWeight="700"
            textAnchor="middle"
            x={center.x}
            y={center.y - 4}
          >
            {targetFirm.ticker}
          </text>
          <text
            fill="#c3c3cc"
            fontSize="12"
            textAnchor="middle"
            x={center.x}
            y={center.y + 20}
          >
            target firm
          </text>
        </g>

        {outgoing.map((entry, index) => (
          <FirmNode
            alpha={entry.alpha}
            key={entry.firm.id}
            label={entry.firm.ticker}
            sector={entry.firm.sector}
            x={rightNodes[index].x}
            y={rightNodes[index].y}
          />
        ))}

        <text fill="#707070" fontSize="13" fontWeight="600" x="56" y="82">
          Sources pointing to {targetFirm.ticker}
        </text>
        <text fill="#707070" fontSize="13" fontWeight="600" x="712" y="82">
          Targets from {targetFirm.ticker}
        </text>
      </svg>
    </div>
  );
}

function layoutColumn(count: number, x: number) {
  const gap = count <= 1 ? 0 : 76;
  const start = 270 - ((count - 1) * gap) / 2;
  return Array.from({ length: count }, (_, index) => ({
    x,
    y: start + index * gap
  }));
}

function Edge({
  source,
  target,
  alpha
}: {
  source: { x: number; y: number };
  target: { x: number; y: number };
  alpha: number;
}) {
  const width = 1.5 + alpha * 6;
  const opacity = 0.24 + alpha * 0.72;

  return (
    <g>
      <line
        markerEnd="url(#ego-arrow)"
        stroke={chartColors.mercuryBlue}
        strokeLinecap="round"
        strokeOpacity={opacity}
        strokeWidth={width}
        x1={source.x}
        x2={target.x}
        y1={source.y}
        y2={target.y}
      />
      <text
        fill="#1e293b"
        fontSize="11"
        fontWeight="700"
        style={{ textShadow: "0px 0px 4px white" }}
        textAnchor="middle"
        x={(source.x + target.x) / 2}
        y={(source.y + target.y) / 2 - 8}
      >
        {alpha.toFixed(2)}
      </text>
    </g>
  );
}

function FirmNode({
  x,
  y,
  label,
  sector,
  alpha
}: {
  x: number;
  y: number;
  label: string;
  sector: string;
  alpha: number;
}) {
  return (
    <g>
      <circle cx={x} cy={y} fill="#f5f5f7" r="42" stroke="#e8e8ed" />
      <text
        fill="#1d1d1f"
        fontSize="18"
        fontWeight="700"
        textAnchor="middle"
        x={x}
        y={y - 8}
      >
        {label}
      </text>
      <text fill="#707070" fontSize="10" textAnchor="middle" x={x} y={y + 10}>
        {sector}
      </text>
      <foreignObject height="24" width="72" x={x - 36} y={y + 14}>
        <div className="flex h-6 items-center justify-center text-[10px] font-bold text-slate-800 [text-shadow:0px_0px_4px_white]">
          <MathText math={`\\alpha\\ ${alpha.toFixed(2)}`} />
        </div>
      </foreignObject>
    </g>
  );
}
