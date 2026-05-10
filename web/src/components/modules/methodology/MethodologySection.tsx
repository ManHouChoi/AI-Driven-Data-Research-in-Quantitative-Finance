"use client";

import { type ReactNode, useMemo, useState } from "react";
import clsx from "clsx";
import { motion } from "framer-motion";
import {
  Braces,
  CircleDot,
  GitBranch,
  Layers3,
  ScanText
} from "lucide-react";
import { MathText } from "@/components/ui/MathText";
import {
  item1aHierarchyExample,
  item1aParagraphRecordJson
} from "@/lib/constants/item1aExample";

const methodologySteps = [
  {
    id: "text",
    title: "Raw 10-K Text",
    subtitle: "Item 1A paragraph extraction",
    description:
      "Risk-factor passages are segmented into paragraph units and normalized into the exact input shape used by the live inference path.",
    equation: "p = clean(Item 1A paragraph)",
    equationMath: "p=\\operatorname{clean}(\\text{Item 1A paragraph})",
    output: "Normalized paragraph",
    metricLabel: "Text unit",
    metricValue: "1 paragraph",
    Icon: ScanText,
    visual: "text"
  },
  {
    id: "embedding",
    title: "MiniLM Embedding",
    subtitle: "Semantic encoding",
    description:
      "The paragraph becomes e_p, a dense all-MiniLM-L6-v2 vector that keeps supplier, liquidity, legal, demand, and governance risks comparable.",
    equation: "e_p = f_phi(c_p) in R^384",
    equationMath: "\\mathbf{e}_p = f_\\phi(c_p) \\in \\mathbb{R}^{384}",
    output: "Dense vector in R^384",
    metricLabel: "Feature space",
    metricValue: "384 dims",
    Icon: Braces,
    visual: "embedding"
  },
  {
    id: "umap",
    title: "UMAP Reduction",
    subtitle: "Neighborhood projection",
    description:
      "The semantic vector is projected into a lower-dimensional inspection space while centroid scoring remains anchored in the original embedding space.",
    equation: "z_p = UMAP(e_p)",
    equationMath: "z_p=\\operatorname{UMAP}(e_p)",
    output: "2D/3D semantic coordinate",
    metricLabel: "Map view",
    metricValue: "theta = 0.45",
    metricMath: "\\theta=0.45",
    Icon: Layers3,
    visual: "umap"
  },
  {
    id: "clusters",
    title: "HDBSCAN Clustering",
    subtitle: "Theme discovery",
    description:
      "Dense neighborhoods form meso risk themes, while sparse observations remain available for taxonomy drift and emerging risk discovery.",
    equation: "cluster(z_p) -> k",
    equationMath: "\\operatorname{cluster}(z_p)\\rightarrow k",
    output: "Risk theme membership",
    metricLabel: "Density rule",
    metricValue: "adaptive",
    Icon: GitBranch,
    visual: "clusters"
  },
  {
    id: "centroid",
    title: "Centroid Assignment",
    subtitle: "Taxonomy scoring",
    description:
      "The paragraph embedding is compared with pre-computed meso and macro centroids so the user sees ranked semantic matches.",
    equation: "rank_k cos(e_p, c_k)",
    equationMath: "\\operatorname{rank}_k\\cos(e_p,\\mathbf{c}_k)",
    output: "Ranked meso/macro labels",
    metricLabel: "Score range",
    metricValue: "[-1, 1]",
    Icon: CircleDot,
    visual: "centroid"
  }
] as const;

const datasetExamples = [
  {
    id: "ops-01",
    ticker: "AAPL",
    label: "Supply Chain Disruption",
    parent: "Supply and production",
    cluster: "Operating Fragility",
    clusterId: "operations",
    clusterCount: 884,
    pointCount: 312,
    coordinates: { x: 0.4, y: -2.7, z: 0.5 },
    raw:
      "We rely on third-party suppliers and contract manufacturers. Component shortages, logistics delays, or production interruptions could materially affect our ability to meet customer demand.",
    normalized:
      "rely third party suppliers contract manufacturers component shortages logistics delays production interruptions meet customer demand",
    tokens: ["suppliers", "component", "logistics", "production", "demand"],
    embeddingPreview: [0.18, -0.04, 0.31, 0.09, -0.12, 0.26, 0.16, -0.07],
    topCentroids: [
      ["Supply Chain Disruption", 0.872],
      ["Production Capacity Risk", 0.641],
      ["Vendor Concentration", 0.598]
    ]
  },
  {
    id: "debt-01",
    ticker: "LVS",
    label: "Debt Covenant Compliance",
    parent: "Financing constraints",
    cluster: "Debt & Covenants",
    clusterId: "debt",
    clusterCount: 575,
    pointCount: 349,
    coordinates: { x: 1.7, y: 2.1, z: 0.4 },
    raw:
      "Our credit facilities contain restrictive covenants. A decline in operating cash flow or failure to satisfy leverage tests could limit borrowing capacity or trigger repayment obligations.",
    normalized:
      "credit facilities restrictive covenants operating cash flow leverage tests borrowing capacity repayment obligations",
    tokens: ["covenants", "cash flow", "leverage", "borrowing", "repayment"],
    embeddingPreview: [-0.06, 0.22, 0.14, -0.18, 0.34, 0.11, -0.03, 0.27],
    topCentroids: [
      ["Debt Covenant Compliance", 0.881],
      ["Debt Maturity Schedule", 0.677],
      ["Fixed Obligation Exposure", 0.612]
    ]
  },
  {
    id: "mkt-01",
    ticker: "WMT",
    label: "Demand Cyclicality",
    parent: "Demand and macro shocks",
    cluster: "Market Exposure",
    clusterId: "market",
    clusterCount: 931,
    pointCount: 355,
    coordinates: { x: -2.4, y: -1.5, z: 0.2 },
    raw:
      "Consumer spending may weaken during inflationary periods or macroeconomic slowdowns. Reduced demand, price sensitivity, and inventory imbalances could pressure revenue growth.",
    normalized:
      "consumer spending inflationary periods macroeconomic slowdowns reduced demand price sensitivity inventory imbalances revenue growth",
    tokens: ["consumer", "inflation", "demand", "inventory", "revenue"],
    embeddingPreview: [0.12, 0.05, -0.21, 0.29, 0.17, -0.09, 0.24, 0.08],
    topCentroids: [
      ["Demand Cyclicality", 0.864],
      ["Interest Rate Sensitivity", 0.621],
      ["Commodity Price Exposure", 0.576]
    ]
  }
] as const;

type MethodologyStep = (typeof methodologySteps)[number];
type DatasetExample = (typeof datasetExamples)[number];

const layoutTransition = { type: "spring", stiffness: 360, damping: 34 } as const;

const methodologyHighlightTerms: Record<string, readonly string[]> = {
  text: [
    "Macroeconomic and Industry Risks",
    "global and regional economic conditions",
    "global supply chain"
  ],
  embedding: ["international operations", "global supply chain", "net sales"],
  umap: ["R^384", "coordinate", "UMAP"],
  clusters: ["Operating Fragility", "Debt & Covenants", "Market Exposure"],
  centroid: ["Supply Chain Disruption", "Debt Covenant Compliance", "Demand Cyclicality"]
};

export function MethodologySection() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [exampleIndex, setExampleIndex] = useState(0);
  const activeStep = methodologySteps[activeIndex];
  const example = datasetExamples[exampleIndex];
  const conversion = useMemo(
    () => getStepConversion(activeStep.id, example),
    [activeStep.id, example]
  );

  return (
    <section
      className="border-b border-apple-mist bg-apple-fog px-4 py-24 sm:px-6 lg:px-8"
      id="methodology"
    >
      <div className="mx-auto max-w-[1200px]">
        <div>
            <p className="mb-5 text-sm font-semibold text-apple-ink">
            02 / Dynamic Taxonomy Construction
          </p>
          <h2 className="max-w-4xl font-display text-5xl font-semibold leading-none text-apple-ink sm:text-7xl">
            From filing text to taxonomy signal.
          </h2>
          <p className="mt-6 max-w-3xl text-xl leading-8 text-apple-graphite">
            Pick a sample risk record, then click through the pipeline to see
            what each stage receives and what it emits.
          </p>
        </div>

        <motion.div
          layout
          className="mt-12 rounded-[28px] bg-white p-4 sm:p-7"
          transition={layoutTransition}
        >
          <div className="mb-7 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
            <div>
              <p className="text-sm font-semibold text-apple-graphite">
                Dataset example
              </p>
              <h3 className="mt-2 text-3xl font-semibold leading-tight text-apple-ink">
                {example.label}
              </h3>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              {datasetExamples.map((item, index) => (
                <button
                  className={clsx(
                    "rounded-[18px] px-4 py-3 text-left transition duration-300",
                    index === exampleIndex
                      ? "bg-apple-ink text-white"
                      : "bg-apple-fog text-apple-graphite hover:bg-apple-mist hover:text-apple-ink"
                  )}
                  key={item.id}
                  type="button"
                  onClick={() => setExampleIndex(index)}
                >
                  <span className="block text-xs font-semibold">
                    {item.ticker} · {item.id}
                  </span>
                  <span className="mt-1 block text-sm font-semibold">
                    {item.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <PipelineGraphic
            conversion={conversion}
            example={example}
            step={activeStep}
          />
          <EquationStrip math={activeStep.equationMath} />

          <div className="mt-6 flex flex-row flex-wrap justify-center gap-3">
            {methodologySteps.map((step, index) => (
              <motion.button
                layout
                aria-pressed={index === activeIndex}
                className={clsx(
                  "min-w-[178px] rounded-[20px] p-4 text-left transition duration-300",
                  index === activeIndex
                    ? "bg-apple-ink text-white"
                    : "bg-apple-fog text-apple-graphite hover:bg-apple-mist hover:text-apple-ink"
                )}
                key={step.id}
                transition={layoutTransition}
                type="button"
                onClick={() => setActiveIndex(index)}
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/80 text-apple-ink">
                  <step.Icon className="h-4 w-4" />
                </span>
                <p className="mt-3 text-xs font-semibold">0{index + 1}</p>
                <p className="mt-2 text-sm font-semibold">{step.title}</p>
              </motion.button>
            ))}
          </div>

          <motion.div
            layout
            className="mt-7 rounded-[28px] bg-apple-fog p-6"
            transition={layoutTransition}
          >
            <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-start">
              <div className="max-w-3xl">
                <div className="flex items-center justify-between gap-4">
                  <span className="flex h-12 w-12 items-center justify-center rounded-full bg-apple-ink text-white">
                    <activeStep.Icon className="h-5 w-5" />
                  </span>
                  <span className="text-sm font-semibold text-apple-graphite">
                    0{activeIndex + 1} / 05
                  </span>
                </div>
                <p className="mt-8 text-sm font-semibold text-apple-graphite">
                  {activeStep.subtitle}
                </p>
                <h3 className="mt-2 text-4xl font-semibold leading-tight text-apple-ink">
                  {activeStep.title}
                </h3>
                <p className="mt-5 text-lg leading-8 text-apple-graphite">
                  <HighlightedText
                    terms={methodologyHighlightTerms[activeStep.id]}
                    text={activeStep.description}
                  />
                </p>
              </div>

              <div className="grid w-full gap-3 sm:grid-cols-2 lg:max-w-[420px]">
                <MethodMetric
                  label="Output"
                  value={activeStep.output}
                />
                <MethodMetric
                  label={activeStep.metricLabel}
                  value={activeStep.metricValue}
                />
              </div>
            </div>

            <ConversionPanel
              conversion={conversion}
              terms={methodologyHighlightTerms[activeStep.id]}
            />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

function getStepConversion(stepId: string, example: DatasetExample) {
  if (stepId === "text") {
    return {
      inputLabel: "Input",
      inputValue: `${item1aHierarchyExample.heading}\n${item1aHierarchyExample.inputExcerpt}`,
      outputLabel: "Output paragraph record",
      outputValue: item1aParagraphRecordJson,
      note: "The economic heading is preserved, while the boilerplate Item 1A header is omitted from the paragraph record."
    };
  }

  if (stepId === "embedding") {
    return {
      inputLabel: "Input tokens",
      inputValue: example.tokens.join(" · "),
      outputLabel: "Embedding preview",
      outputValue: `[${example.embeddingPreview.map((value) => value.toFixed(2)).join(", ")}] ...`,
      note: "The real model vector is 384-dimensional; this card shows a compact preview."
    };
  }

  if (stepId === "umap") {
    return {
      inputLabel: "Input",
      inputValue: "e_p in R^384",
      outputLabel: "Output coordinate",
      outputValue: `(${example.coordinates.x.toFixed(1)}, ${example.coordinates.y.toFixed(1)}, ${example.coordinates.z.toFixed(1)})`,
      note: `This coordinate matches the public UMAP demo record ${example.id}.`
    };
  }

  if (stepId === "clusters") {
    return {
      inputLabel: "Input coordinate",
      inputValue: `z_p = (${example.coordinates.x.toFixed(1)}, ${example.coordinates.y.toFixed(1)}, ${example.coordinates.z.toFixed(1)})`,
      outputLabel: "Output cluster",
      outputValue: `${example.cluster} · ${example.parent}`,
      note: `${example.pointCount} points map to this local label; ${example.clusterCount} points sit in the broader cluster.`
    };
  }

  return {
    inputLabel: "Input",
    inputValue: "e_p compared with c_k centroid vectors",
    outputLabel: "Output ranking",
    outputValue: example.topCentroids
      .map(([label, score], index) => `${index + 1}. ${label}: ${score.toFixed(3)}`)
      .join("  "),
    note: "The live NLP engine uses this same scoring idea when it reports cosine similarity."
  };
}

function MethodMetric({
  label,
  value,
  math
}: {
  label: string;
  value: string;
  math?: string;
}) {
  return (
    <motion.div
      layout
      className="rounded-[20px] bg-white p-4"
      transition={layoutTransition}
    >
      <p className="text-xs font-semibold uppercase text-apple-graphite">
        {label}
      </p>
      <p className="mt-2 font-mono text-lg leading-8 text-apple-ink">
        {math ? <MathText math={math} /> : value}
      </p>
    </motion.div>
  );
}

function EquationStrip({ math }: { math: string }) {
  return (
    <div className="w-full flex justify-center py-4">
      <div className="thin-scrollbar max-w-full overflow-x-auto whitespace-nowrap rounded-full bg-apple-fog px-5 py-3 text-center font-mono text-xl text-apple-ink">
        <MathText math={math} />
      </div>
    </div>
  );
}

function ConversionPanel({
  conversion,
  terms
}: {
  conversion: ReturnType<typeof getStepConversion>;
  terms: readonly string[];
}) {
  return (
    <motion.div
      layout
      className="mt-6 rounded-[22px] bg-white p-4"
      transition={layoutTransition}
    >
      <div className="grid gap-3">
        <ConversionBlock
          label={conversion.inputLabel}
          terms={terms}
          value={conversion.inputValue}
        />
        <div className="flex items-center gap-3 text-xs font-semibold uppercase text-apple-graphite">
          <span className="h-px flex-1 bg-apple-mist" />
          converts to
          <span className="h-px flex-1 bg-apple-mist" />
        </div>
        <ConversionBlock
          label={conversion.outputLabel}
          terms={terms}
          value={conversion.outputValue}
        />
      </div>
      <p className="mt-4 text-sm leading-6 text-apple-graphite">
        <HighlightedText terms={terms} text={conversion.note} />
      </p>
    </motion.div>
  );
}

function ConversionBlock({
  label,
  value,
  terms
}: {
  label: string;
  value: string;
  terms: readonly string[];
}) {
  const multiline = value.includes("\n");

  return (
    <motion.div
      layout
      className="rounded-[18px] bg-apple-fog p-4"
      transition={layoutTransition}
    >
      <p className="text-xs font-semibold uppercase text-apple-graphite">
        {label}
      </p>
      {multiline ? (
        <pre className="mt-2 whitespace-pre-wrap font-mono text-lg leading-8 text-apple-ink">
          <HighlightedText terms={terms} text={value} />
        </pre>
      ) : (
        <p className="mt-2 text-lg leading-8 text-apple-ink">
          <HighlightedText terms={terms} text={value} />
        </p>
      )}
    </motion.div>
  );
}

function PipelineGraphic({
  step,
  example,
  conversion
}: {
  step: MethodologyStep;
  example: DatasetExample;
  conversion: ReturnType<typeof getStepConversion>;
}) {
  return (
    <motion.div
      layout
      className="relative min-h-[560px] w-full overflow-hidden rounded-[28px] bg-apple-fog p-5 sm:p-8"
      transition={layoutTransition}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_28%_18%,rgba(255,255,255,0.95),rgba(255,255,255,0)_36%),radial-gradient(circle_at_78%_76%,rgba(210,210,215,0.46),rgba(210,210,215,0)_34%)]" />
      <div className="relative">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase text-apple-graphite">
              input-output linkage
            </p>
            <p className="mt-1 text-xl font-semibold text-apple-ink">
              {conversion.inputLabel} maps to {conversion.outputLabel}
            </p>
          </div>
          <span className="hidden rounded-full bg-white px-4 py-2 text-xs font-semibold uppercase text-apple-graphite sm:inline">
            {step.subtitle}
          </span>
        </div>
        <StepRelationGraphic example={example} step={step} />
      </div>
    </motion.div>
  );
}

function StepRelationGraphic({
  step,
  example
}: {
  step: MethodologyStep;
  example: DatasetExample;
}) {
  if (step.id === "text") {
    return (
      <RelationShell
        left={<Item1AInput example={example} />}
        right={<StructuredTextOutput example={example} />}
        step={step}
      />
    );
  }

  if (step.id === "embedding") {
    return (
      <RelationShell
        left={<TokenInput example={example} />}
        right={<VectorOutput example={example} />}
        step={step}
      />
    );
  }

  if (step.id === "umap") {
    return (
      <RelationShell
        left={<VectorInput example={example} />}
        right={<CoordinateOutput example={example} />}
        step={step}
      />
    );
  }

  if (step.id === "clusters") {
    return (
      <RelationShell
        left={<CoordinateInput example={example} />}
        right={<ClusterOutput example={example} />}
        step={step}
      />
    );
  }

  return (
    <RelationShell
      left={<CentroidInput example={example} />}
      right={<RankingOutput example={example} />}
      step={step}
    />
  );
}

function RelationShell({
  step,
  left,
  right
}: {
  step: MethodologyStep;
  left: ReactNode;
  right: ReactNode;
}) {
  return (
    <motion.div
      layout
      className="relative min-h-[460px]"
      transition={layoutTransition}
    >
      <svg
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 hidden h-full w-full lg:block"
        preserveAspectRatio="none"
        viewBox="0 0 100 100"
      >
        <path
          className="pipeline-dash"
          d="M31 32 C42 32 43 26 50 26 S61 32 70 32"
          fill="none"
          stroke="#5266eb"
          strokeLinecap="round"
          strokeWidth="0.9"
        />
        <path
          className="pipeline-dash"
          d="M31 52 C42 52 43 52 50 52 S61 52 70 52"
          fill="none"
          stroke="#1d1d1f"
          strokeLinecap="round"
          strokeOpacity="0.45"
          strokeWidth="0.7"
        />
        <path
          className="pipeline-dash"
          d="M31 72 C42 72 43 79 50 79 S61 72 70 72"
          fill="none"
          stroke="#5266eb"
          strokeLinecap="round"
          strokeOpacity="0.6"
          strokeWidth="0.7"
        />
      </svg>

      <div className="relative grid gap-5 lg:grid-cols-[1fr_132px_1fr] lg:items-center">
        {left}

        <div className="flex flex-col items-center justify-center gap-3">
          <span className="pipeline-node-rise flex h-16 w-16 items-center justify-center rounded-full bg-apple-ink text-white">
            <step.Icon className="h-7 w-7" />
          </span>
          <div className="rounded-[18px] bg-white px-4 py-3 text-center">
            <p className="text-xs font-semibold uppercase text-apple-graphite">
              transform
            </p>
            <p className="mt-1 text-xs font-semibold text-apple-ink">
              {step.output}
            </p>
          </div>
        </div>

        {right}
      </div>
    </motion.div>
  );
}

function RelationCard({
  title,
  eyebrow,
  children
}: {
  title: string;
  eyebrow: string;
  children: ReactNode;
}) {
  return (
    <motion.div
      layout
      className="rounded-[24px] border border-apple-mist bg-white p-5 shadow-[0_24px_70px_rgba(0,0,0,0.08)]"
      transition={layoutTransition}
    >
      <p className="text-xs font-semibold uppercase text-apple-graphite">
        {eyebrow}
      </p>
      <h4 className="mt-1 text-xl font-semibold text-apple-ink">{title}</h4>
      <div className="mt-5">{children}</div>
    </motion.div>
  );
}

function Item1AInput({ example }: { example: DatasetExample }) {
  const [subheading, rawText] = item1aHierarchyExample.inputExcerpt.split("\n");

  return (
    <RelationCard eyebrow="input" title="SEC Item 1A excerpt">
      <div className="relative overflow-hidden rounded-[18px] bg-apple-fog p-4">
        <div className="methodology-scan absolute left-0 right-0 top-7 h-12 bg-gradient-to-b from-transparent via-[#5266eb]/[0.18] to-transparent" />
        <p className="mt-3 text-sm font-semibold text-apple-ink">
          {item1aHierarchyExample.heading}
        </p>
        <p className="mt-3 text-lg leading-8 text-apple-graphite">
          <HighlightedText terms={methodologyHighlightTerms.text} text={subheading} />
        </p>
        <p className="mt-3 text-lg leading-8 text-apple-graphite">
          <HighlightedText terms={methodologyHighlightTerms.text} text={rawText} />
        </p>
      </div>
    </RelationCard>
  );
}

function StructuredTextOutput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="output" title="Paragraph record">
      <pre className="overflow-hidden whitespace-pre-wrap rounded-[18px] bg-apple-fog p-4 font-mono text-lg leading-8 text-apple-ink"><HighlightedText
        terms={methodologyHighlightTerms.text}
        text={item1aParagraphRecordJson}
      /></pre>
    </RelationCard>
  );
}

function TokenInput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="input" title="Cleaned text unit">
      <div className="rounded-[18px] bg-apple-fog p-4">
        <p className="text-lg leading-8 text-apple-ink">
          <HighlightedText
            terms={methodologyHighlightTerms.embedding}
            text={example.normalized}
          />
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {example.tokens.map((token) => (
            <motion.span
              layout
              className="rounded-full bg-[#5266eb]/10 px-3 py-2 text-xs font-semibold text-apple-ink"
              key={token}
              transition={layoutTransition}
            >
              <HighlightedText
                terms={methodologyHighlightTerms.embedding}
                text={token}
              />
            </motion.span>
          ))}
        </div>
      </div>
    </RelationCard>
  );
}

function VectorOutput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="output" title="Dense embedding vector">
      <EmbeddingProjectionVisual example={example} />
      <p className="mt-4 font-mono text-xs text-apple-graphite">
        384-dimensional dense vector preview
      </p>
    </RelationCard>
  );
}

const embeddingParticles = Array.from({ length: 42 }, (_, index) => ({
  id: `particle-${index}`,
  delay: (index % 14) * 0.11,
  startY: ((index * 37) % 160) - 80,
  midX: ((index * 29) % 180) - 30,
  midY: ((index * 43) % 180) - 90,
  endY: ((index * 19) % 150) - 75,
  size: 3 + (index % 4)
}));

function EmbeddingProjectionVisual({ example }: { example: DatasetExample }) {
  const maxMagnitude = Math.max(
    ...example.embeddingPreview.map((value) => Math.abs(value))
  );

  return (
    <div className="relative h-72 overflow-hidden rounded-[18px] bg-apple-fog [perspective:900px]">
      <motion.div
        animate={{ opacity: [0.92, 0.52, 0.92], scale: [1, 0.97, 1] }}
        className="absolute left-4 top-4 w-[48%] rounded-[16px] border border-apple-mist bg-white p-4"
        transition={{ duration: 3.4, ease: "easeInOut", repeat: Infinity }}
      >
        <p className="font-mono text-[11px] uppercase text-apple-graphite">
          cleaned text
        </p>
        <p className="mt-3 line-clamp-5 text-sm leading-6 text-apple-ink">
          {example.normalized}
        </p>
      </motion.div>

      <div className="absolute inset-0 [transform-style:preserve-3d]">
        {embeddingParticles.map((particle) => (
          <motion.span
            animate={{
              opacity: [0, 1, 0.25, 0],
              x: [-158, particle.midX, 176],
              y: [particle.startY, particle.midY, particle.endY],
              rotateX: [0, 52, 0],
              rotateY: [0, -38, 0],
              scale: [0.7, 1.35, 0.75]
            }}
            className="absolute left-1/2 top-1/2 rounded-full bg-[#5266eb] shadow-[0_0_14px_rgba(82,102,235,0.75)]"
            key={particle.id}
            style={{ height: particle.size, width: particle.size }}
            transition={{
              delay: particle.delay,
              duration: 3.2,
              ease: "easeInOut",
              repeat: Infinity
            }}
          />
        ))}
      </div>

      <motion.div
        animate={{ rotateX: [8, -8, 8], rotateY: [-13, 13, -13] }}
        className="absolute bottom-4 right-4 top-4 w-[46%] rounded-[18px] border border-[#5266eb]/20 bg-white/88 p-4 shadow-[0_22px_60px_rgba(82,102,235,0.18)] [transform-style:preserve-3d]"
        transition={{ duration: 5.8, ease: "easeInOut", repeat: Infinity }}
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <p className="font-mono text-[11px] uppercase text-apple-graphite">
            vector array
          </p>
          <span className="rounded-full bg-[#5266eb]/10 px-2 py-1 font-mono text-[10px] text-apple-ink">
            384 dims
          </span>
        </div>
        <div className="grid gap-2">
          {example.embeddingPreview.map((value, index) => {
            const width = `${Math.max(18, (Math.abs(value) / maxMagnitude) * 100)}%`;
            return (
              <div
                className="grid grid-cols-[34px_1fr_44px] items-center gap-2"
                key={index}
              >
                <span className="font-mono text-[10px] text-apple-graphite">
                  d{String(index + 1).padStart(3, "0")}
                </span>
                <span className="h-1.5 overflow-hidden rounded-full bg-apple-mist">
                  <motion.span
                    animate={{ width }}
                    className={clsx(
                      "block h-full rounded-full",
                      value >= 0 ? "bg-apple-ink" : "bg-[#5266eb]"
                    )}
                    initial={{ width: "14%" }}
                    transition={{
                      delay: index * 0.08,
                      duration: 0.85,
                      ease: "easeOut"
                    }}
                  />
                </span>
                <span className="text-right font-mono text-[10px] text-apple-ink">
                  {value.toFixed(2)}
                </span>
              </div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}

function VectorInput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="input" title="MiniLM vector stream">
      <EmbeddingProjectionVisual example={example} />
      <p className="mt-4 font-mono text-xs text-apple-graphite">
        animated input to UMAP from the same 384-dimensional embedding
      </p>
    </RelationCard>
  );
}

function CoordinateOutput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="output" title="UMAP coordinate">
      <UMAPProjectionVisual example={example} />
    </RelationCard>
  );
}

function CoordinateInput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="input" title="Projected neighborhood">
      <UMAPNeighborhoodVisual example={example} />
    </RelationCard>
  );
}

function ClusterOutput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="output" title="Density cluster assignment">
      <DensityClusterVisual example={example} />
    </RelationCard>
  );
}

function CentroidInput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="input" title="Embedding vs centroids">
      <CentroidSimilarityVisual example={example} />
    </RelationCard>
  );
}

function RankingOutput({ example }: { example: DatasetExample }) {
  return (
    <RelationCard eyebrow="output" title="Ranked taxonomy labels">
      <TaxonomyRankingVisual example={example} />
    </RelationCard>
  );
}

const umapPeerPoints = [
  { id: "u1", x: 18, y: 58, cluster: "operations" },
  { id: "u2", x: 25, y: 45, cluster: "operations" },
  { id: "u3", x: 34, y: 61, cluster: "operations" },
  { id: "u4", x: 44, y: 37, cluster: "market" },
  { id: "u5", x: 56, y: 64, cluster: "operations" },
  { id: "u6", x: 66, y: 42, cluster: "debt" },
  { id: "u7", x: 76, y: 53, cluster: "debt" },
  { id: "u8", x: 84, y: 31, cluster: "market" },
  { id: "u9", x: 71, y: 73, cluster: "operations" }
] as const;

const umapProjectionParticles = Array.from({ length: 18 }, (_, index) => ({
  id: `umap-projection-${index}`,
  delay: index * 0.08,
  y: ((index * 31) % 112) - 56,
  scale: 0.74 + (index % 5) * 0.08
}));

function UMAPProjectionVisual({ example }: { example: DatasetExample }) {
  const projectedPoints = [
    { id: "p1", x: -26, y: 20, z: 0.1, cluster: "operations" },
    { id: "p2", x: -18, y: -14, z: 0.3, cluster: "operations" },
    { id: "p3", x: -8, y: 25, z: 0.7, cluster: "operations" },
    { id: "p4", x: 18, y: -18, z: 0.2, cluster: "market" },
    { id: "p5", x: 30, y: 10, z: 0.5, cluster: "debt" },
    { id: "p6", x: 8, y: 28, z: -0.2, cluster: "operations" },
    { id: "p7", x: 38, y: -30, z: 0.9, cluster: "market" }
  ] as const;
  const selectedProjection = {
    x: Math.min(74, Math.max(18, 50 + example.coordinates.x * 8)),
    y: Math.min(76, Math.max(18, 50 - example.coordinates.y * 7 - example.coordinates.z * 10))
  };

  return (
    <div className="relative h-72 overflow-hidden rounded-[18px] bg-apple-fog p-4 [perspective:900px]">
      <div className="absolute bottom-4 left-4 top-4 w-[31%] rounded-[16px] border border-apple-mist bg-white p-3">
        <div className="flex h-full items-center gap-1.5 pb-3 pt-8">
          {example.embeddingPreview.map((value, index) => (
            <motion.span
              animate={{
                height: [
                  `${30 + index * 4}%`,
                  `${48 + Math.abs(value) * 132}%`,
                  `${30 + index * 4}%`
                ],
                opacity: [0.76, 1, 0.76]
              }}
              className={clsx(
                "w-full rounded-full",
                value >= 0 ? "bg-apple-ink" : "bg-[#5266eb]"
              )}
              key={index}
              transition={{
                delay: index * 0.06,
                duration: 2.2,
                ease: "easeInOut",
                repeat: Infinity
              }}
            />
          ))}
        </div>
        <span className="absolute left-3 top-3 rounded-full bg-[#5266eb]/10 px-2 py-1 font-mono text-[10px] text-apple-ink">
          384d
        </span>
      </div>

      <div className="absolute bottom-4 left-[35%] top-4 w-[22%]">
        <motion.div
          animate={{ scale: [0.94, 1.04, 0.94], opacity: [0.72, 1, 0.72] }}
          className="absolute left-1/2 top-1/2 h-24 w-12 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#5266eb]/40 bg-white shadow-[0_0_34px_rgba(82,102,235,0.2)]"
          transition={{ duration: 2.7, ease: "easeInOut", repeat: Infinity }}
        />
        <div className="absolute left-1/2 top-1/2 h-px w-full -translate-x-1/2 bg-apple-mist" />
        <div className="absolute left-1/2 top-[16%] -translate-x-1/2 rounded-full bg-white px-3 py-1 font-mono text-[10px] text-apple-graphite">
          UMAP
        </div>
        <div className="absolute bottom-[16%] left-1/2 -translate-x-1/2 rounded-full bg-[#5266eb]/10 px-3 py-1 font-mono text-[10px] text-apple-ink">
          384d -&gt; 3d
        </div>
        {umapProjectionParticles.map((particle) => (
          <motion.span
            animate={{
              opacity: [0, 1, 0],
              x: ["-70%", "45%", "165%"],
              y: [particle.y, particle.y * 0.2, particle.y * -0.18],
              rotateZ: [0, 42, 0],
              scale: [particle.scale, particle.scale * 1.55, particle.scale * 0.7]
            }}
            className="absolute left-1/2 top-1/2 h-1.5 w-1.5 rounded-full bg-[#5266eb] shadow-[0_0_12px_rgba(82,102,235,0.72)]"
            key={particle.id}
            transition={{
              delay: particle.delay,
              duration: 2.8,
              ease: "easeInOut",
              repeat: Infinity
            }}
          />
        ))}
      </div>

      <div className="absolute bottom-4 right-4 top-4 w-[39%] overflow-hidden rounded-[16px] border border-apple-mist bg-white">
        <div className="absolute inset-x-5 bottom-5 top-16 [transform-style:preserve-3d]">
          <motion.div
            animate={{ rotateX: [62, 58, 62], rotateZ: [-36, -40, -36] }}
            className="absolute inset-2 rounded-[18px] border border-apple-mist bg-[linear-gradient(90deg,rgba(210,210,215,0.45)_1px,transparent_1px),linear-gradient(0deg,rgba(210,210,215,0.45)_1px,transparent_1px)] bg-[length:34px_34px]"
            style={{ transform: "rotateX(60deg) rotateZ(-38deg)" }}
            transition={{ duration: 5, ease: "easeInOut", repeat: Infinity }}
          />
          <span className="absolute bottom-8 left-8 h-px w-[72%] rotate-[-16deg] bg-apple-mist" />
          <span className="absolute bottom-8 left-8 h-px w-[52%] rotate-[-72deg] bg-apple-mist" />
          <span className="absolute bottom-8 left-8 h-px w-[42%] rotate-[-42deg] bg-[#5266eb]/60" />
          {projectedPoints.map((point, index) => {
            const left = `${Math.min(84, Math.max(12, 50 + point.x * 0.74))}%`;
            const top = `${Math.min(82, Math.max(14, 50 + point.y * 0.62 - point.z * 12))}%`;

            return (
              <motion.span
                animate={{
                  opacity: [0.42, 1, 0.42],
                  scale: [0.82, 1 + point.z * 0.24, 0.82],
                  y: [0, -point.z * 7, 0]
                }}
                className={clsx(
                  "absolute h-2.5 w-2.5 rounded-full shadow-[0_0_12px_rgba(82,102,235,0.28)]",
                  point.cluster === example.clusterId
                    ? "bg-[#5266eb]"
                    : "bg-apple-ink/25"
                )}
                key={point.id}
                style={{ left, top }}
                transition={{
                  delay: index * 0.1,
                  duration: 2.8,
                  ease: "easeInOut",
                  repeat: Infinity
                }}
              />
            );
          })}
          <motion.span
            animate={{
              boxShadow: [
                "0 0 0 0 rgba(82,102,235,0.32)",
                "0 0 0 18px rgba(82,102,235,0)",
                "0 0 0 0 rgba(82,102,235,0)"
              ],
              scale: [0.96, 1.08, 0.96]
            }}
            className="absolute h-9 w-9 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#5266eb] bg-[#5266eb]/15"
            style={{
              left: `${selectedProjection.x}%`,
              top: `${selectedProjection.y}%`
            }}
            transition={{ duration: 2.4, ease: "easeOut", repeat: Infinity }}
          />
        </div>
        <div className="absolute right-3 top-3 rounded-[14px] bg-apple-fog px-3 py-2">
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            3d coordinate
          </p>
          <p className="mt-1 font-mono text-[11px] text-apple-ink">
            <MathText
              math={`z_p=(${example.coordinates.x.toFixed(1)},${example.coordinates.y.toFixed(1)},${example.coordinates.z.toFixed(1)})`}
            />
          </p>
        </div>
        <div className="absolute bottom-3 left-3 flex gap-1 font-mono text-[10px] text-apple-graphite">
          <span>x</span>
          <span>y</span>
          <span>z</span>
        </div>
      </div>
    </div>
  );
}

function UMAPNeighborhoodVisual({ example }: { example: DatasetExample }) {
  const selectedLeft = `${Math.min(86, Math.max(12, 50 + example.coordinates.x * 9))}%`;
  const selectedTop = `${Math.min(82, Math.max(14, 50 - example.coordinates.y * 9))}%`;
  const sameClusterCount = umapPeerPoints.filter(
    (point) => point.cluster === example.clusterId
  ).length;

  return (
    <div className="relative h-64 overflow-hidden rounded-[18px] bg-apple-fog">
      <span className="absolute bottom-8 left-8 right-8 h-px bg-apple-mist" />
      <span className="absolute bottom-8 left-8 top-8 w-px bg-apple-mist" />
      <motion.span
        animate={{ scale: [0.88, 1.08, 0.88], opacity: [0.38, 0.72, 0.38] }}
        className="absolute h-32 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#5266eb]/50 bg-[#5266eb]/10"
        style={{ left: selectedLeft, top: selectedTop }}
        transition={{ duration: 3, ease: "easeInOut", repeat: Infinity }}
      />
      {umapPeerPoints.map((point, index) => (
        <motion.span
          animate={{ y: [0, index % 2 === 0 ? -3 : 3, 0] }}
          className={clsx(
            "absolute h-3 w-3 rounded-full",
            point.cluster === example.clusterId ? "bg-[#5266eb]" : "bg-apple-ink/30"
          )}
          key={point.id}
          style={{ left: `${point.x}%`, top: `${point.y}%` }}
          transition={{
            delay: index * 0.1,
            duration: 2.4,
            ease: "easeInOut",
            repeat: Infinity
          }}
        />
      ))}
      <span
        className="absolute h-8 w-8 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#5266eb] bg-white"
        style={{ left: selectedLeft, top: selectedTop }}
      />
      <div className="absolute bottom-3 left-3 right-3 grid grid-cols-2 gap-2">
        <div className="rounded-[14px] bg-white px-3 py-2">
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            local density
          </p>
          <p className="mt-1 text-sm font-semibold text-apple-ink">
            {sameClusterCount} near points
          </p>
        </div>
        <div className="rounded-[14px] bg-white px-3 py-2">
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            projected id
          </p>
          <p className="mt-1 font-mono text-sm text-apple-ink">{example.id}</p>
        </div>
      </div>
    </div>
  );
}

const densityClusters = [
  {
    id: "operations",
    label: "operating",
    className:
      "left-[8%] top-[12%] h-32 w-40 border-[#5266eb]/45 bg-[#5266eb]/10"
  },
  {
    id: "debt",
    label: "debt",
    className:
      "right-[8%] top-[18%] h-36 w-40 border-apple-ink/25 bg-white"
  },
  {
    id: "market",
    label: "market",
    className:
      "bottom-[10%] left-[30%] h-32 w-44 border-apple-mist bg-white/60"
  }
] as const;

const densityPoints = [
  { x: 18, y: 30, cluster: "operations" },
  { x: 28, y: 39, cluster: "operations" },
  { x: 20, y: 50, cluster: "operations" },
  { x: 36, y: 34, cluster: "operations" },
  { x: 62, y: 32, cluster: "debt" },
  { x: 72, y: 44, cluster: "debt" },
  { x: 66, y: 56, cluster: "debt" },
  { x: 81, y: 36, cluster: "debt" },
  { x: 43, y: 68, cluster: "market" },
  { x: 53, y: 75, cluster: "market" },
  { x: 37, y: 80, cluster: "market" },
  { x: 58, y: 66, cluster: "market" },
  { x: 84, y: 78, cluster: "noise" },
  { x: 12, y: 78, cluster: "noise" }
] as const;

function DensityClusterVisual({ example }: { example: DatasetExample }) {
  return (
    <div>
      <div className="relative h-64 overflow-hidden rounded-[18px] bg-apple-fog">
        {densityClusters.map((cluster, index) => (
          <motion.span
            animate={{ scale: cluster.id === example.clusterId ? [0.96, 1.05, 0.96] : [0.98, 1.01, 0.98] }}
            className={clsx(
              "absolute rounded-full border-2",
              cluster.className
            )}
            key={cluster.id}
            transition={{
              delay: index * 0.18,
              duration: 3.2,
              ease: "easeInOut",
              repeat: Infinity
            }}
          />
        ))}
        {densityPoints.map((point, index) => (
          <motion.span
            animate={{ opacity: point.cluster === "noise" ? [0.28, 0.6, 0.28] : [0.72, 1, 0.72] }}
            className={clsx(
              "absolute h-3 w-3 rounded-full",
              point.cluster === example.clusterId
                ? "bg-[#5266eb]"
                : point.cluster === "noise"
                  ? "bg-apple-graphite"
                  : "bg-apple-ink/55"
            )}
            key={`${point.x}-${point.y}`}
            style={{ left: `${point.x}%`, top: `${point.y}%` }}
            transition={{
              delay: index * 0.08,
              duration: 2.6,
              ease: "easeInOut",
              repeat: Infinity
            }}
          />
        ))}
        <div className="absolute left-4 top-4 rounded-[16px] bg-white px-3 py-2">
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            hdbscan output
          </p>
          <p className="mt-1 text-sm font-semibold text-apple-ink">
            {example.cluster}
          </p>
        </div>
        <div className="absolute bottom-4 right-4 rounded-[16px] bg-white px-3 py-2">
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            support
          </p>
          <p className="mt-1 font-mono text-sm text-apple-ink">
            n={example.pointCount}
          </p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <div className="rounded-[16px] bg-apple-fog p-3">
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            assigned theme
          </p>
          <p className="mt-1 text-sm font-semibold text-apple-ink">
            {example.cluster}
          </p>
        </div>
        <div className="rounded-[16px] bg-apple-fog p-3">
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            macro parent
          </p>
          <p className="mt-1 text-sm font-semibold text-apple-ink">
            {example.parent}
          </p>
        </div>
      </div>
    </div>
  );
}

const centroidNodePositions = [
  "left-[7%] top-[18%]",
  "right-[7%] top-[20%]",
  "bottom-[10%] left-[16%]"
] as const;

function CentroidSimilarityVisual({ example }: { example: DatasetExample }) {
  return (
    <div className="relative h-72 overflow-hidden rounded-[18px] bg-apple-fog">
      <motion.span
        animate={{ rotate: [0, 360] }}
        className="absolute left-1/2 top-1/2 h-44 w-44 -translate-x-1/2 -translate-y-1/2 rounded-full border border-apple-mist"
        transition={{ duration: 12, ease: "linear", repeat: Infinity }}
      />
      <span className="absolute left-1/2 top-1/2 flex h-20 w-20 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-apple-ink text-sm font-semibold text-white shadow-[0_18px_40px_rgba(0,0,0,0.16)]">
        <MathText math="e_p" />
      </span>
      {example.topCentroids.map(([label, score], index) => (
        <motion.div
          animate={{ scale: index === 0 ? [1, 1.08, 1] : [1, 1.03, 1] }}
          className={clsx(
            "absolute flex h-16 w-16 flex-col items-center justify-center rounded-full bg-white font-mono text-xs text-apple-ink shadow-[0_14px_36px_rgba(0,0,0,0.08)]",
            centroidNodePositions[index]
          )}
          key={label}
          transition={{
            delay: index * 0.2,
            duration: 2.6,
            ease: "easeInOut",
            repeat: Infinity
          }}
        >
          <span>c{index + 1}</span>
          <span className="mt-0.5 text-[10px] text-apple-graphite">
            {score.toFixed(2)}
          </span>
        </motion.div>
      ))}
      <motion.span
        animate={{ opacity: [0.35, 1, 0.35], scaleX: [0.72, 1, 0.72] }}
        className="absolute left-[28%] top-[36%] h-0.5 w-[24%] rotate-[18deg] origin-right rounded-full bg-[#5266eb]"
        transition={{ duration: 2.4, ease: "easeInOut", repeat: Infinity }}
      />
      <span className="absolute right-[27%] top-[38%] h-px w-[24%] -rotate-[18deg] bg-apple-mist" />
      <span className="absolute bottom-[30%] left-[31%] h-px w-[24%] -rotate-[24deg] bg-apple-mist" />
      <div className="absolute bottom-4 left-4 right-4 rounded-[16px] bg-white p-3">
        <p className="font-mono text-[10px] uppercase text-apple-graphite">
          cosine similarity
        </p>
        <div className="mt-2 grid gap-2">
          {example.topCentroids.map(([label, score], index) => (
            <div
              className="grid grid-cols-[28px_1fr_42px] items-center gap-2"
              key={label}
            >
              <span className="font-mono text-[10px] text-apple-graphite">
                c{index + 1}
              </span>
              <span className="h-1.5 overflow-hidden rounded-full bg-apple-mist">
                <motion.span
                  animate={{ width: `${score * 100}%` }}
                  className="block h-full rounded-full bg-[#5266eb]"
                  initial={{ width: "12%" }}
                  transition={{ delay: index * 0.1, duration: 0.8, ease: "easeOut" }}
                />
              </span>
              <span className="text-right font-mono text-[10px] text-apple-ink">
                {score.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TaxonomyRankingVisual({ example }: { example: DatasetExample }) {
  return (
    <div className="rounded-[18px] bg-apple-fog p-4">
      <div className="mb-4 grid grid-cols-[1fr_auto] items-center gap-3 rounded-[16px] bg-white px-3 py-2">
        <div>
          <p className="font-mono text-[10px] uppercase text-apple-graphite">
            selected macro
          </p>
          <p className="mt-1 text-sm font-semibold text-apple-ink">
            {example.parent}
          </p>
        </div>
        <span className="rounded-full bg-[#5266eb]/10 px-3 py-1 font-mono text-[10px] text-apple-ink">
          {example.clusterCount} pts
        </span>
      </div>
      <div className="space-y-4">
        {example.topCentroids.map(([label, score], index) => (
          <motion.div
            animate={{ y: [0, index === 0 ? -2 : 0, 0] }}
            key={label}
            transition={{
              delay: index * 0.12,
              duration: 2.8,
              ease: "easeInOut",
              repeat: Infinity
            }}
          >
            <div className="flex justify-between gap-4 text-xs font-semibold text-apple-graphite">
              <span>
                {index + 1}. {label}
              </span>
              <span>{score.toFixed(3)}</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-apple-mist">
              <motion.span
                animate={{ width: `${score * 100}%` }}
                className="block h-full rounded-full bg-[#5266eb]"
                initial={{ width: "10%" }}
                transition={{ delay: index * 0.12, duration: 0.9, ease: "easeOut" }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function VectorBars({ values }: { values: readonly number[] }) {
  const maxMagnitude = Math.max(...values.map((value) => Math.abs(value)));

  return (
    <div className="flex h-48 items-center gap-2 rounded-[18px] bg-apple-fog p-4">
      {values.map((value, index) => {
        const height = Math.max(24, (Math.abs(value) / maxMagnitude) * 150);
        return (
          <span className="flex h-full flex-1 items-center" key={index}>
            <span
              className={clsx(
                "methodology-bar w-full rounded-full",
                value >= 0 ? "bg-apple-ink" : "bg-[#5266eb]/70"
              )}
              style={{
                height,
                animationDelay: `${index * 0.08}s`
              }}
            />
          </span>
        );
      })}
    </div>
  );
}

function MiniScatter({ example }: { example: DatasetExample }) {
  const peerPoints = [
    [17, 62],
    [23, 46],
    [31, 57],
    [43, 35],
    [55, 64],
    [64, 42],
    [75, 52],
    [82, 31],
    [70, 72]
  ];
  const left = `${50 + example.coordinates.x * 10}%`;
  const top = `${50 - example.coordinates.y * 10}%`;

  return (
    <div className="relative h-56 overflow-hidden rounded-[18px] bg-apple-fog">
      <span className="absolute bottom-8 left-8 right-8 h-px bg-apple-mist" />
      <span className="absolute bottom-8 left-8 top-8 w-px bg-apple-mist" />
      {peerPoints.map(([peerLeft, peerTop], index) => (
        <span
          className={clsx(
            "absolute h-3 w-3 rounded-full",
            index % 3 === 0 ? "bg-apple-ink" : "bg-[#5266eb]/70"
          )}
          key={`${peerLeft}-${peerTop}`}
          style={{ left: `${peerLeft}%`, top: `${peerTop}%` }}
        />
      ))}
      <span
        className="methodology-drift absolute h-8 w-8 rounded-full border-2 border-[#5266eb] bg-[#5266eb]/[0.12]"
        style={{ left, top }}
      />
    </div>
  );
}

function TextGraphic({ example }: { example: DatasetExample }) {
  return (
    <div className="relative w-full max-w-[560px] rounded-[28px] bg-white p-7">
      <div className="methodology-scan absolute left-0 right-0 top-10 h-12 bg-gradient-to-b from-transparent via-[#0071e3]/[0.16] to-transparent" />
      <p className="text-sm font-semibold text-apple-graphite">
        {example.ticker} Item 1A
      </p>
      <p className="mt-6 text-lg leading-8 text-apple-ink">{example.raw}</p>
      <div className="mt-8 flex flex-wrap gap-2">
        {example.tokens.map((token) => (
          <span
            className="rounded-full bg-[#0071e3]/10 px-3 py-2 text-xs font-semibold text-apple-ink"
            key={token}
          >
            {token}
          </span>
        ))}
      </div>
    </div>
  );
}

function EmbeddingGraphic({ example }: { example: DatasetExample }) {
  const maxMagnitude = Math.max(
    ...example.embeddingPreview.map((value) => Math.abs(value))
  );

  return (
    <div className="w-full max-w-[580px] rounded-[28px] bg-white p-7">
      <div className="flex h-72 items-center gap-2 rounded-[24px] bg-apple-fog p-5">
        {example.embeddingPreview.map((value, index) => {
          const height = Math.max(28, (Math.abs(value) / maxMagnitude) * 190);
          return (
            <span className="flex h-full flex-1 items-center" key={index}>
              <span
                className={clsx(
                  "methodology-bar w-full rounded-full",
                  value >= 0 ? "bg-apple-ink" : "bg-[#0071e3]/70"
                )}
                style={{
                  height,
                  animationDelay: `${index * 0.08}s`
                }}
              />
            </span>
          );
        })}
      </div>
      <div className="mt-6 grid grid-cols-4 gap-2">
        {example.embeddingPreview.map((value, index) => (
          <span
            className="rounded-full bg-apple-fog px-3 py-2 text-center font-mono text-xs text-apple-graphite"
            key={index}
          >
            d{index + 1}: {value.toFixed(2)}
          </span>
        ))}
      </div>
    </div>
  );
}

function UMAPGraphic({ example }: { example: DatasetExample }) {
  const peerPoints = [
    [17, 62],
    [23, 46],
    [31, 57],
    [43, 35],
    [55, 64],
    [64, 42],
    [75, 52],
    [82, 31],
    [70, 72]
  ];
  const left = `${50 + example.coordinates.x * 10}%`;
  const top = `${50 - example.coordinates.y * 10}%`;

  return (
    <div className="relative h-[440px] w-full max-w-[620px] overflow-hidden rounded-[28px] bg-white">
      <span className="absolute bottom-12 left-10 right-10 h-px bg-apple-mist" />
      <span className="absolute bottom-12 left-10 top-10 w-px bg-apple-mist" />
      <span
        className="methodology-drift absolute h-12 w-12 rounded-full border-2 border-[#0071e3] bg-[#0071e3]/[0.12]"
        style={{ left, top }}
      />
      {peerPoints.map(([peerLeft, peerTop], index) => (
        <span
          className={clsx(
            "absolute h-4 w-4 rounded-full",
            index % 3 === 0 ? "bg-apple-ink" : "bg-[#0071e3]/70"
          )}
          key={`${peerLeft}-${peerTop}`}
          style={{ left: `${peerLeft}%`, top: `${peerTop}%` }}
        />
      ))}
      <div className="absolute right-8 top-8 rounded-[20px] bg-apple-fog px-4 py-3">
        <p className="text-xs font-semibold uppercase text-apple-graphite">
          {example.id}
        </p>
        <p className="mt-1 font-mono text-sm text-apple-ink">
          ({example.coordinates.x.toFixed(1)}, {example.coordinates.y.toFixed(1)},{" "}
          {example.coordinates.z.toFixed(1)})
        </p>
      </div>
    </div>
  );
}

function ClusterGraphic({ example }: { example: DatasetExample }) {
  const dots = [
    [24, 30],
    [32, 42],
    [21, 49],
    [62, 32],
    [72, 44],
    [66, 56],
    [44, 66],
    [52, 74],
    [38, 78]
  ];

  return (
    <div className="relative h-[440px] w-full max-w-[620px] rounded-[28px] bg-white">
      <span className="methodology-pulse absolute left-[12%] top-[15%] h-40 w-44 rounded-full border-2 border-[#0071e3]/[0.45] bg-[#0071e3]/10" />
      <span className="methodology-pulse absolute right-[12%] top-[19%] h-44 w-48 rounded-full border-2 border-apple-ink/25 bg-apple-ink/5 [animation-delay:0.6s]" />
      <span className="methodology-pulse absolute bottom-[12%] left-[30%] h-36 w-52 rounded-full border-2 border-apple-mist bg-apple-fog [animation-delay:1.1s]" />
      {dots.map(([left, top], index) => (
        <span
          className="absolute h-4 w-4 rounded-full bg-apple-ink"
          key={`${left}-${top}`}
          style={{ left: `${left}%`, top: `${top}%` }}
        />
      ))}
      <div className="absolute left-8 top-8 rounded-[22px] bg-apple-fog p-4">
        <p className="text-xs font-semibold uppercase text-apple-graphite">
          assigned cluster
        </p>
        <p className="mt-1 text-xl font-semibold text-apple-ink">
          {example.cluster}
        </p>
        <p className="mt-2 text-sm text-apple-graphite">
          {example.clusterCount} public demo observations
        </p>
      </div>
    </div>
  );
}

function CentroidGraphic({ example }: { example: DatasetExample }) {
  return (
    <div className="relative h-[440px] w-full max-w-[620px] rounded-[28px] bg-white">
      <span className="methodology-orbit absolute left-1/2 top-1/2 h-44 w-44 -translate-x-1/2 -translate-y-1/2 rounded-full border border-apple-mist" />
      <span className="absolute left-1/2 top-1/2 flex h-24 w-24 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-apple-ink text-sm font-semibold text-white">
        <MathText math="e_p" />
      </span>
      {example.topCentroids.map(([label, score], index) => (
        <CentroidNode
          key={label}
          className={[
            "left-[9%] top-[22%]",
            "right-[8%] top-[24%]",
            "bottom-[14%] left-[19%]"
          ][index]}
          label={`c${index + 1}`}
          score={score}
        />
      ))}
      <span className="absolute left-[29%] top-[36%] h-px w-[24%] rotate-[18deg] bg-[#0071e3]" />
      <span className="absolute right-[28%] top-[38%] h-px w-[23%] -rotate-[18deg] bg-apple-mist" />
      <span className="absolute bottom-[29%] left-[31%] h-px w-[24%] -rotate-[24deg] bg-apple-mist" />
      <div className="absolute bottom-8 left-8 right-8 rounded-[22px] bg-apple-fog p-4">
        {example.topCentroids.map(([label, score]) => (
          <div className="mb-3 last:mb-0" key={label}>
            <div className="flex justify-between gap-4 text-xs font-semibold text-apple-graphite">
              <span>{label}</span>
              <span>{score.toFixed(3)}</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-apple-mist">
              <span
                className="methodology-score block h-full rounded-full bg-[#0071e3]"
                style={{ width: `${score * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CentroidNode({
  className,
  label,
  score
}: {
  className: string;
  label: string;
  score: number;
}) {
  return (
    <span
      className={clsx(
        "absolute flex h-16 w-16 flex-col items-center justify-center rounded-full bg-apple-fog text-sm font-semibold text-apple-ink",
        className
      )}
    >
      <span>{label}</span>
      <span className="font-mono text-[10px] text-apple-graphite">
        {score.toFixed(2)}
      </span>
    </span>
  );
}

function HighlightedText({
  text,
  terms
}: {
  text: string;
  terms: readonly string[];
}) {
  const activeTerms = terms.filter((term) =>
    text.toLowerCase().includes(term.toLowerCase())
  );

  if (activeTerms.length === 0) {
    return <>{text}</>;
  }

  const pattern = new RegExp(`(${activeTerms.map(escapeRegExp).join("|")})`, "gi");

  return (
    <>
      {text.split(pattern).map((part, index) => {
        const highlighted = activeTerms.some(
          (term) => term.toLowerCase() === part.toLowerCase()
        );

        return highlighted ? (
          <motion.span
            layout
            className="rounded-md bg-[#f7d774]/70 px-1 text-apple-ink"
            key={`${part}-${index}`}
            transition={layoutTransition}
          >
            {part}
          </motion.span>
        ) : (
          part
        );
      })}
    </>
  );
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
