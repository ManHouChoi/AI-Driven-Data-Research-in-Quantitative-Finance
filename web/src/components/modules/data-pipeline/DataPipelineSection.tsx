"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";
import { motion } from "framer-motion";
import {
  Code2,
  Database,
  FileText,
  Globe2,
  ScanText,
  Table2
} from "lucide-react";
import { MathText } from "@/components/ui/MathText";
import {
  item1aHierarchyExample,
  item1aParagraphRecordJson
} from "@/lib/constants/item1aExample";

const pipelineSteps = [
  {
    id: "filing",
    title: "10-K filing",
    subtitle: "Apple Inc. FY2023 Form 10-K",
    inputLabel: "Input",
    inputValue: "SEC accession + company CIK",
    outputLabel: "Output",
    outputValue: "Filing metadata with Item 1A anchor",
    artifact: "sec_filing_index.csv",
    equation: "filing_id -> primary_doc.html",
    equationMath: "\\mathrm{filing\\_id}\\rightarrow\\mathrm{primary\\_doc.html}",
    Icon: FileText
  },
  {
    id: "html",
    title: "HTML document",
    subtitle: "SEC inline filing source",
    inputLabel: "Input",
    inputValue: "<html><body>...ITEM 1A. RISK FACTORS...</body></html>",
    outputLabel: "Output",
    outputValue: "DOM tree with section_anchor, headings, and text blocks",
    artifact: "aapl_2023_10k.html",
    equation: "html -> DOM nodes",
    equationMath: "\\mathrm{html}\\rightarrow\\mathrm{DOM\\ nodes}",
    Icon: Code2
  },
  {
    id: "item1a",
    title: "Item 1A extraction",
    subtitle: "Risk-factor boundary detection",
    inputLabel: "Input",
    inputValue: "DOM headings + sibling text nodes",
    outputLabel: "Output",
    outputValue: "section_anchor, Heading, Subheading, RawText records",
    artifact: "item1a_segments.csv",
    equation: "c_p = concat(Heading_p, Subheading_p, RawText_p)",
    equationMath:
      "c_p=\\operatorname{concat}(\\mathrm{Heading}_p,\\mathrm{Subheading}_p,\\mathrm{RawText}_p)",
    Icon: ScanText
  },
  {
    id: "master",
    title: "Master Paragraph Aggregation",
    subtitle: "All firm-year paragraph corpus",
    inputLabel: "Input",
    inputValue: "Validated Item 1A paragraph records across firm-years",
    outputLabel: "Output",
    outputValue:
      "ticker, cik, fiscal_year, filing_date, paragraph_id, section_anchor, heading, subheading, raw_text",
    artifact: "paragraph_master.csv",
    equation: "records -> paragraph_master.csv",
    equationMath: "\\mathrm{records}\\rightarrow\\mathrm{paragraph\\_master.csv}",
    Icon: Table2
  },
  {
    id: "corpus",
    title: "Pre-Clustering Corpus Export",
    subtitle: "Stable taxonomy input pack",
    inputLabel: "Input",
    inputValue: "paragraph_master.csv",
    outputLabel: "Output",
    outputValue: "clean_text, metadata, and lineage keys for embedding jobs",
    artifact: "taxonomy_corpus.jsonl",
    equation: "paragraph_master.csv -> taxonomy_corpus.jsonl",
    equationMath:
      "\\mathrm{paragraph\\_master.csv}\\rightarrow\\mathrm{taxonomy\\_corpus.jsonl}",
    Icon: Database
  }
] as const;

type PipelineStep = (typeof pipelineSteps)[number];

const layoutTransition = { type: "spring", stiffness: 360, damping: 34 } as const;

const pipelineHighlightTerms: Record<string, readonly string[]> = {
  filing: ["SEC accession", "company CIK", "primary_doc", "ITEM 1A. RISK FACTORS"],
  html: ["ITEM 1A. RISK FACTORS", "international operations"],
  item1a: [
    "ITEM 1A. RISK FACTORS",
    "Macroeconomic and Industry Risks",
    "global and regional economic conditions",
    "global supply chain"
  ],
  master: ["paragraph_master.csv", "ITEM 1A. RISK FACTORS", "AAPL", "LVS", "MSFT"],
  corpus: ["taxonomy_corpus.jsonl", "paragraph_master.csv", "clean_text", "lineage"]
};

export function DataPipelineSection() {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeStep = pipelineSteps[activeIndex];

  const nextArtifact = useMemo(
    () => pipelineSteps[Math.min(activeIndex + 1, pipelineSteps.length - 1)].artifact,
    [activeIndex]
  );

  return (
    <section
      className="border-b border-apple-mist bg-white px-4 py-24 sm:px-6 lg:px-8"
      id="data-pipeline"
    >
      <div className="mx-auto max-w-[1200px]">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
          <div>
            <p className="mb-5 text-sm font-semibold text-apple-ink">
              01 / Data Pre-Processing
            </p>
            <h2 className="max-w-4xl font-display text-5xl font-semibold leading-none text-apple-ink sm:text-7xl">
              From 10-K filings to research-ready files.
            </h2>
          </div>
          <p className="text-xl leading-8 text-apple-graphite">
            This project starts with an SEC filing, parses the HTML, isolates
            Item 1A risk text, and aggregates every extracted paragraph into a
            master pre-clustering corpus.
          </p>
        </div>

        <div className="mt-12 flex flex-col gap-6">
          <motion.div
            layout
            className="w-full overflow-hidden rounded-[30px] bg-apple-fog p-4 sm:p-7"
            transition={layoutTransition}
          >
            <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div>
                <p className="text-sm font-semibold text-apple-graphite">
                  Example walk-through
                </p>
                <h3 className="mt-2 text-3xl font-semibold leading-tight text-apple-ink">
                  {activeStep.subtitle}
                </h3>
              </div>
              <motion.div
                layout
                className="rounded-[20px] bg-white px-4 py-3"
                transition={layoutTransition}
              >
                <p className="text-xs font-semibold uppercase text-apple-graphite">
                  active artifact
                </p>
                <p className="mt-1 font-mono text-sm text-apple-ink">
                  {activeStep.artifact}
                </p>
              </motion.div>
            </div>

            <PipelineLinkageGraphic activeIndex={activeIndex} step={activeStep} />
          </motion.div>

          <div className="flex flex-row flex-wrap justify-center gap-3">
            {pipelineSteps.map((step, index) => (
              <motion.button
                layout
                aria-pressed={index === activeIndex}
                className={clsx(
                  "group min-w-[180px] rounded-[22px] p-4 text-left transition duration-300",
                  index === activeIndex
                    ? "bg-apple-ink text-white"
                    : "bg-apple-fog text-apple-graphite hover:bg-apple-mist hover:text-apple-ink"
                )}
                key={step.id}
                transition={layoutTransition}
                type="button"
                onClick={() => setActiveIndex(index)}
              >
                <span className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-3">
                    <span
                      className={clsx(
                        "flex h-10 w-10 items-center justify-center rounded-full",
                        index === activeIndex
                          ? "bg-white text-apple-ink"
                          : "bg-white text-mercury-blue"
                      )}
                    >
                      <step.Icon className="h-5 w-5" />
                    </span>
                    <span>
                      <span className="block text-xs font-semibold">
                        0{index + 1}
                      </span>
                      <span className="mt-1 block text-sm font-semibold">
                        {step.title}
                      </span>
                    </span>
                  </span>
                </span>
              </motion.button>
            ))}
          </div>

          <motion.div layout transition={layoutTransition}>
            <div className="mt-6 grid gap-3 md:grid-cols-3">
              <ArtifactCard label={activeStep.inputLabel} value={activeStep.inputValue} />
              <ArtifactCard
                label="Transform"
                math={activeStep.equationMath}
                value={activeStep.equation}
              />
              <ArtifactCard label={activeStep.outputLabel} value={activeStep.outputValue} />
            </div>

            <div className="mt-4 rounded-[22px] bg-white p-4">
              <div className="flex items-center gap-3 text-xs font-semibold uppercase text-apple-graphite">
                <span className="h-px flex-1 bg-apple-mist" />
                writes forward to
                <span className="h-px flex-1 bg-apple-mist" />
              </div>
              <p className="mt-3 text-center font-mono text-sm text-apple-ink">
                {nextArtifact}
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function PipelineLinkageGraphic({
  activeIndex,
  step
}: {
  activeIndex: number;
  step: PipelineStep;
}) {
  return (
    <motion.div
      layout
      className="relative min-h-[470px] overflow-hidden rounded-[26px] bg-white p-5"
      transition={layoutTransition}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_24%_18%,rgba(82,102,235,0.12),rgba(82,102,235,0)_34%),radial-gradient(circle_at_78%_78%,rgba(245,245,247,0.95),rgba(245,245,247,0)_38%)]" />
      <svg
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full"
        preserveAspectRatio="none"
        viewBox="0 0 100 100"
      >
        <path
          className="pipeline-dash"
          d="M27 35 C40 35 40 24 53 24 S68 30 74 30"
          fill="none"
          stroke="#5266eb"
          strokeLinecap="round"
          strokeWidth="0.8"
        />
        <path
          className="pipeline-dash"
          d="M27 54 C42 54 42 61 55 61 S68 54 74 54"
          fill="none"
          stroke="#1d1d1f"
          strokeLinecap="round"
          strokeOpacity="0.45"
          strokeWidth="0.6"
        />
        <path
          className="pipeline-dash"
          d="M27 72 C41 72 43 83 57 83 S69 76 74 76"
          fill="none"
          stroke="#5266eb"
          strokeLinecap="round"
          strokeOpacity="0.6"
          strokeWidth="0.6"
        />
      </svg>

      <div className="relative grid min-h-[430px] gap-5 lg:grid-cols-[1fr_160px_1fr] lg:items-center">
        <PipelineDocumentCard activeIndex={activeIndex} />

        <div className="flex flex-col items-center justify-center gap-4">
          <span className="pipeline-node-rise flex h-16 w-16 items-center justify-center rounded-full bg-apple-ink text-white">
            <step.Icon className="h-7 w-7" />
          </span>
          <div className="rounded-[18px] bg-apple-fog px-4 py-3 text-center">
            <p className="text-xs font-semibold uppercase text-apple-graphite">
              stage
            </p>
            <p className="mt-1 text-sm font-semibold text-apple-ink">
              {step.title}
            </p>
          </div>
        </div>

        <PipelineOutputCard activeIndex={activeIndex} />
      </div>
    </motion.div>
  );
}

function PipelineDocumentCard({ activeIndex }: { activeIndex: number }) {
  const activeStep = pipelineSteps[activeIndex];

  return (
    <motion.div
      layout
      className="rounded-[24px] border border-apple-mist bg-white p-5 shadow-[0_24px_70px_rgba(0,0,0,0.08)]"
      transition={layoutTransition}
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase text-apple-graphite">
            source
          </p>
          <p className="mt-1 text-lg font-semibold text-apple-ink">
            AAPL 2023 Form 10-K
          </p>
        </div>
        <Globe2 className="h-5 w-5 text-mercury-blue" />
      </div>

      <div className="space-y-3">
        <div
          className={clsx(
            "rounded-[16px] p-3 transition",
            activeIndex === 0 ? "bg-[#5266eb]/10" : "bg-apple-fog"
          )}
        >
          <p className="font-mono text-lg leading-8 text-apple-graphite">
            <HighlightedText
              terms={pipelineHighlightTerms[activeStep.id]}
              text="accession: 0000320193-23-000106"
            />
          </p>
          <p className="mt-1 font-mono text-lg leading-8 text-apple-graphite">
            <HighlightedText
              terms={pipelineHighlightTerms[activeStep.id]}
              text="primary_doc: aapl-20230930.htm"
            />
          </p>
        </div>
        <div
          className={clsx(
            "rounded-[16px] p-3 transition",
            activeIndex === 1 ? "bg-[#5266eb]/10" : "bg-apple-fog"
          )}
        >
          <p className="font-mono text-lg leading-8 text-apple-ink">
            <HighlightedText
              terms={pipelineHighlightTerms[activeStep.id]}
              text="<span>ITEM 1A. RISK FACTORS</span>"
            />
          </p>
          <p className="mt-1 font-mono text-lg leading-8 text-apple-graphite">
            <HighlightedText
              terms={pipelineHighlightTerms[activeStep.id]}
              text="<p>The Company has international operations...</p>"
            />
          </p>
        </div>
        <div
          className={clsx(
            "rounded-[16px] p-3 transition",
            activeIndex === 2 ? "bg-[#5266eb]/10" : "bg-apple-fog"
          )}
        >
          <p className="text-sm font-semibold text-apple-ink">
            {item1aHierarchyExample.heading}
          </p>
          <p className="mt-2 text-lg leading-8 text-apple-graphite">
            <HighlightedText
              terms={pipelineHighlightTerms[activeStep.id]}
              text={item1aHierarchyExample.inputExcerpt}
            />
          </p>
        </div>
        <div
          className={clsx(
            "rounded-[16px] p-3 transition",
            activeIndex >= 3 ? "bg-[#5266eb]/10" : "bg-apple-fog"
          )}
        >
          <div className="grid grid-cols-[62px_54px_54px_96px_1fr] gap-1 font-mono text-xs leading-6 text-apple-graphite">
            <span>ticker</span>
            <span>year</span>
            <span>pid</span>
            <span>anchor</span>
            <span>text</span>
            <span>AAPL</span>
            <span>2023</span>
            <span>p001</span>
            <span>ITEM 1A...</span>
            <span>supplier...</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function PipelineOutputCard({ activeIndex }: { activeIndex: number }) {
  const activeStep = pipelineSteps[activeIndex];

  if (activeIndex <= 1) {
    return (
      <motion.div
        layout
        className="rounded-[24px] border border-apple-mist bg-white p-5 shadow-[0_24px_70px_rgba(0,0,0,0.08)]"
        transition={layoutTransition}
      >
        <p className="text-xs font-semibold uppercase text-apple-graphite">
          output object
        </p>
        <pre className="mt-4 overflow-hidden whitespace-pre-wrap font-mono text-lg leading-8 text-apple-ink">
          <HighlightedText
            terms={pipelineHighlightTerms[activeStep.id]}
            text={`{
  "document": "aapl-20230930.htm",
  "form": "10-K",
  "section_anchor": "ITEM 1A. RISK FACTORS",
  "html_blocks": 428
}`}
          />
        </pre>
      </motion.div>
    );
  }

  if (activeIndex === 2) {
    return (
      <motion.div
        layout
        className="rounded-[24px] border border-apple-mist bg-white p-5 shadow-[0_24px_70px_rgba(0,0,0,0.08)]"
        transition={layoutTransition}
      >
        <p className="text-xs font-semibold uppercase text-apple-graphite">
          extracted records
        </p>
        <pre className="mt-4 overflow-hidden whitespace-pre-wrap rounded-[16px] bg-apple-fog p-4 font-mono text-lg leading-8 text-apple-ink">
          <HighlightedText
            terms={pipelineHighlightTerms[activeStep.id]}
            text={item1aParagraphRecordJson}
          />
        </pre>
      </motion.div>
    );
  }

  return (
    <motion.div
      layout
      className="rounded-[24px] border border-apple-mist bg-white p-5 shadow-[0_24px_70px_rgba(0,0,0,0.08)]"
      transition={layoutTransition}
    >
      {activeIndex === 3 ? (
        <ParagraphMasterPreview terms={pipelineHighlightTerms[activeStep.id]} />
      ) : (
        <CorpusExportPreview terms={pipelineHighlightTerms[activeStep.id]} />
      )}
    </motion.div>
  );
}

function ParagraphMasterPreview({ terms }: { terms: readonly string[] }) {
  const rows = [
    [
      "AAPL",
      "0000320193",
      "2023",
      "AAPL-2023-001",
      "ITEM 1A. RISK FACTORS",
      "Macroeconomic and Industry Risks",
      "The Company has international operations with a large and complex global supply chain..."
    ],
    [
      "LVS",
      "0001300514",
      "2023",
      "LVS-2023-014",
      "ITEM 1A. RISK FACTORS",
      "Operating and regulatory risks",
      "Our integrated resorts depend on travel demand, gaming concessions, and Macau visitation..."
    ],
    [
      "MSFT",
      "0000789019",
      "2024",
      "MSFT-2024-009",
      "ITEM 1A. RISK FACTORS",
      "Cloud infrastructure risks",
      "Service interruptions, cybersecurity incidents, and capacity constraints could affect customers..."
    ]
  ];

  return (
    <>
      <p className="text-xs font-semibold uppercase text-apple-graphite">
        paragraph_master.csv
      </p>
      <div className="thin-scrollbar mt-4 overflow-x-auto rounded-[16px] border border-apple-mist">
        <div className="min-w-[980px]">
          <div className="grid grid-cols-[82px_120px_92px_150px_190px_210px_1fr] bg-apple-fog px-3 py-2 font-mono text-sm leading-6 text-apple-graphite">
            <span>ticker</span>
            <span>cik</span>
            <span>fiscal_year</span>
            <span>paragraph_id</span>
            <span>section_anchor</span>
            <span>heading</span>
            <span>raw_text</span>
          </div>
          {rows.map((row) => (
            <div
              className="grid grid-cols-[82px_120px_92px_150px_190px_210px_1fr] border-t border-apple-mist px-3 py-2 font-mono text-sm leading-6 text-apple-ink"
              key={row[3]}
            >
              {row.map((cell) => (
                <span className="truncate pr-3" key={cell}>
                  <HighlightedText terms={terms} text={cell} />
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function CorpusExportPreview({ terms }: { terms: readonly string[] }) {
  const rows = [
    ["source_file", "paragraph_master.csv"],
    ["records", "all extracted Item 1A paragraphs across firm-years"],
    ["embedding_input", "clean_text"],
    ["lineage", "ticker + fiscal_year + paragraph_id"]
  ];

  return (
    <>
      <p className="text-xs font-semibold uppercase text-apple-graphite">
        taxonomy_corpus.jsonl manifest
      </p>
      <div className="mt-4 overflow-hidden rounded-[16px] border border-apple-mist">
        {rows.map(([field, value]) => (
          <div
            className="grid grid-cols-[150px_1fr] border-b border-apple-mist px-3 py-2 font-mono text-sm leading-6 text-apple-ink last:border-b-0"
            key={field}
          >
            <span className="text-apple-graphite">{field}</span>
            <span>
              <HighlightedText terms={terms} text={value} />
            </span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {["CSV", "JSONL", "pre-clustering", "lineage"].map((label) => (
          <span
            className="rounded-full bg-[#5266eb]/10 px-3 py-2 text-xs font-semibold text-apple-ink"
            key={label}
          >
            {label}
          </span>
        ))}
      </div>
    </>
  );
}

function ArtifactCard({
  label,
  value,
  math
}: {
  label: string;
  value: string;
  math?: string;
}) {
  return (
    <div className="rounded-[20px] bg-white p-4">
      <p className="text-xs font-semibold uppercase text-apple-graphite">
        {label}
      </p>
      <p className="mt-2 text-lg leading-8 text-apple-ink">
        {math ? <MathText math={math} /> : value}
      </p>
    </div>
  );
}

function HighlightedText({
  text,
  terms
}: {
  text: string;
  terms: readonly string[];
}) {
  const activeTerms = terms.filter((term) => text.toLowerCase().includes(term.toLowerCase()));

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
