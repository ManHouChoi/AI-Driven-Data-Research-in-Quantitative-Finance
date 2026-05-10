"use client";

import { useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { SectionHeader } from "@/components/shell/SectionHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { chartColors } from "@/lib/constants/colors";
import { useCaseStudyData } from "@/lib/data/loadPortfolioReturns";
import type { CaseStudyTicker } from "@/types/portfolio";

const curatedTickers = ["LVS", "NVDA", "BAC", "XOM"];

export function CaseStudy() {
  const { data, isLoading } = useCaseStudyData();
  const [selectedTicker, setSelectedTicker] = useState("LVS");
  const [comparisonTicker, setComparisonTicker] = useState("NVDA");
  const [compareEnabled, setCompareEnabled] = useState(false);

  const tickers = useMemo(
    () =>
      (data?.tickers ?? []).filter((ticker) =>
        curatedTickers.includes(ticker.ticker)
      ),
    [data]
  );
  const selected = useMemo(
    () =>
      tickers.find((ticker) => ticker.ticker === selectedTicker) ??
      tickers[0] ??
      null,
    [selectedTicker, tickers]
  );
  const comparison = useMemo(() => {
    const fallback = selected?.ticker === "NVDA" ? "LVS" : "NVDA";
    return (
      tickers.find(
        (ticker) =>
          ticker.ticker ===
          (comparisonTicker === selected?.ticker ? fallback : comparisonTicker)
      ) ??
      tickers.find((ticker) => ticker.ticker === fallback) ??
      tickers[1] ??
      null
    );
  }, [comparisonTicker, selected?.ticker, tickers]);

  const activePanels = compareEnabled
    ? [selected, comparison].filter(Boolean)
    : [selected].filter(Boolean);

  return (
    <section
      className="border-t border-mercury-lead/20 bg-mercury-slate px-4 py-20 sm:px-6 lg:px-8"
      id="case-study"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-10 flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <SectionHeader
            copy="A firm-level longitudinal view of risk exposure migration and semantic peer proximity during shock years."
            kicker="04 / Longitudinal Case Study"
            title="Firm risk trajectory"
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <label>
              <span className="mb-2 block text-xs text-mercury-silver">
                Primary ticker
              </span>
              <Select
                disabled={isLoading || !data}
                value={selected?.ticker ?? selectedTicker}
                onChange={(event) => setSelectedTicker(event.target.value)}
              >
                {tickers.map((ticker) => (
                  <option key={ticker.ticker} value={ticker.ticker}>
                    {ticker.ticker} · {ticker.archetype ?? ticker.name}
                  </option>
                ))}
              </Select>
            </label>

            {compareEnabled ? (
              <label>
                <span className="mb-2 block text-xs text-mercury-silver">
                  Compare against
                </span>
                <Select
                  disabled={isLoading || !data}
                  value={comparison?.ticker ?? comparisonTicker}
                  onChange={(event) => setComparisonTicker(event.target.value)}
                >
                  {tickers
                    .filter((ticker) => ticker.ticker !== selected?.ticker)
                    .map((ticker) => (
                      <option key={ticker.ticker} value={ticker.ticker}>
                        {ticker.ticker} · {ticker.archetype ?? ticker.name}
                      </option>
                    ))}
                </Select>
              </label>
            ) : null}

            <Button
              className="self-start sm:self-auto"
              variant={compareEnabled ? "primary" : "secondary"}
              onClick={() => setCompareEnabled((value) => !value)}
            >
              {compareEnabled ? "Compare on" : "Compare"}
            </Button>
          </div>
        </div>

        {isLoading ? (
          <Card className="flex h-[440px] items-center justify-center p-4" tone="light">
            <span className="text-sm text-apple-graphite">
              Loading case study...
            </span>
          </Card>
        ) : compareEnabled ? (
          <div className="grid gap-5 lg:grid-cols-2">
            {activePanels.map((ticker) => (
              <CaseStudyPanel compact key={ticker!.ticker} ticker={ticker!} />
            ))}
          </div>
        ) : selected ? (
          <div className="grid gap-5 lg:grid-cols-2">
            <ExposureChart ticker={selected} />
            <TrajectoryChart ticker={selected} />
          </div>
        ) : null}
      </div>
    </section>
  );
}

function CaseStudyPanel({
  ticker,
  compact = false
}: {
  ticker: CaseStudyTicker;
  compact?: boolean;
}) {
  return (
    <div className="space-y-5">
      <div className="rounded-lg bg-white px-4 py-3">
        <p className="text-sm font-semibold text-apple-ink">
          {ticker.ticker} · {ticker.name}
        </p>
        <p className="mt-1 text-xs text-apple-graphite">
          {ticker.archetype} · shock years {ticker.shockYears.join(", ")}
        </p>
      </div>
      <ExposureChart compact={compact} ticker={ticker} />
      <TrajectoryChart compact={compact} ticker={ticker} />
    </div>
  );
}

function ExposureChart({
  ticker,
  compact = false
}: {
  ticker: CaseStudyTicker;
  compact?: boolean;
}) {
  return (
    <Card className="p-4" tone="light">
      <div className="mb-4">
        <p className="font-mono text-xs uppercase text-apple-graphite">
          {ticker.ticker} exposure share, 2006-2024
        </p>
        <p className="mt-1 text-sm text-apple-graphite">
          Macro and meso vector concentration over time.
        </p>
      </div>
      <div className={compact ? "h-[300px]" : "h-[440px]"}>
        <ResponsiveContainer height="100%" width="100%">
          <LineChart
            data={ticker.trajectory}
            margin={{ bottom: 12, left: 8, right: 28, top: 24 }}
          >
            <CartesianGrid stroke="#ededf3" vertical={false} />
            <XAxis
              dataKey="year"
              stroke={chartColors.ink}
              tick={{ fill: chartColors.ink, fontSize: 12 }}
              tickLine={false}
            />
            <YAxis
              stroke={chartColors.ink}
              tick={{ fill: chartColors.ink, fontSize: 12 }}
              tickFormatter={(value) => `${(Number(value) * 100).toFixed(0)}%`}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: chartColors.ink,
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: chartColors.starlight
              }}
              formatter={(value: number, name: string) => [
                `${(value * 100).toFixed(1)}%`,
                name
              ]}
              labelStyle={{ color: chartColors.starlight }}
            />
            <Legend />
            <Line
              dataKey="macroShare"
              dot={!compact}
              name="Top macro exposure"
              stroke={chartColors.mercuryBlue}
              strokeWidth={3}
              type="monotone"
            />
            <Line
              dataKey="mesoShare"
              dot={!compact}
              name="Top meso exposure"
              stroke={chartColors.teal}
              strokeWidth={2}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function TrajectoryChart({
  ticker,
  compact = false
}: {
  ticker: CaseStudyTicker;
  compact?: boolean;
}) {
  const option = useMemo(() => buildTrajectoryOption(ticker), [ticker]);

  return (
    <Card className="p-4" tone="light">
      <div className="mb-4">
        <p className="font-mono text-xs uppercase text-apple-graphite">
          {ticker.ticker} PCA semantic path
        </p>
        <p className="mt-1 text-sm text-apple-graphite">
          Shock-year points are highlighted with nearest semantic peers.
        </p>
      </div>
      <ReactECharts
        className={compact ? "h-[300px] w-full" : "h-[440px] w-full"}
        option={option}
        opts={{ renderer: "canvas" }}
        style={{ height: compact ? 300 : 440, width: "100%" }}
      />
    </Card>
  );
}

function buildTrajectoryOption(ticker: CaseStudyTicker) {
  const trajectory = ticker.trajectory;
  const peerPoints = trajectory.flatMap((point) =>
    point.peers.map((peer) => ({
      ...peer,
      year: point.year
    }))
  );

  return {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: chartColors.ink,
      borderColor: "rgba(255,255,255,0.12)",
      textStyle: { color: chartColors.starlight },
      formatter: (params: { data: unknown[]; seriesName: string }) => {
        const dataPoint = params.data as unknown[];
        if (params.seriesName === "Nearest peers") {
          return `<strong>${dataPoint[2]}</strong><br/>year: ${dataPoint[3]}<br/>cosine: ${Number(dataPoint[4]).toFixed(3)}`;
        }
        return `<strong>${ticker.ticker} ${dataPoint[2]}</strong><br/>nearest peer: ${dataPoint[3]}<br/>cosine: ${Number(dataPoint[4]).toFixed(3)}`;
      }
    },
    grid: {
      left: 44,
      right: 24,
      top: 28,
      bottom: 44
    },
    xAxis: {
      name: "PC1",
      type: "value",
      axisLine: { lineStyle: { color: "#d6d6dc" } },
      splitLine: { lineStyle: { color: "#ededf3" } }
    },
    yAxis: {
      name: "PC2",
      type: "value",
      axisLine: { lineStyle: { color: "#d6d6dc" } },
      splitLine: { lineStyle: { color: "#ededf3" } }
    },
    series: [
      {
        name: "Historical path",
        type: "line",
        data: trajectory.map((point) => [
          point.x,
          point.y,
          point.year,
          point.nearestPeer,
          point.nearestPeerCosine
        ]),
        lineStyle: {
          color: chartColors.mercuryBlue,
          width: 3
        },
        symbolSize: 9
      },
      {
        name: "Shock years",
        type: "scatter",
        symbolSize: 18,
        itemStyle: { color: chartColors.rose },
        data: trajectory
          .filter((point) => ticker.shockYears.includes(point.year))
          .map((point) => [
            point.x,
            point.y,
            point.year,
            point.nearestPeer,
            point.nearestPeerCosine
          ])
      },
      {
        name: "Nearest peers",
        type: "scatter",
        symbolSize: 11,
        itemStyle: { color: chartColors.teal, opacity: 0.72 },
        data: peerPoints.map((peer) => [
          peer.x,
          peer.y,
          peer.ticker,
          peer.year,
          peer.cosine
        ])
      }
    ]
  };
}
