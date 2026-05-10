"use client";

import { motion } from "framer-motion";
import { Activity, AlertCircle, CheckCircle2 } from "lucide-react";
import { TaxonomyBadge } from "@/components/modules/nlp-engine/TaxonomyBadge";
import { Card } from "@/components/ui/Card";
import { MathText } from "@/components/ui/MathText";
import { useInferenceStore } from "@/stores/useInferenceStore";

interface InferenceResultPanelProps {
  processingMessage?: string | null;
  processingStepIndex?: number | null;
  revealResult?: boolean;
}

export function InferenceResultPanel({
  processingMessage = null,
  processingStepIndex = null,
  revealResult = true
}: InferenceResultPanelProps) {
  const status = useInferenceStore((state) => state.status);
  const result = useInferenceStore((state) => state.result);
  const errorMessage = useInferenceStore((state) => state.errorMessage);
  const displayStatus = processingMessage ? "loading" : status;

  return (
    <Card className="h-full p-5" tone="frosted">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-mercury-starlight">
            {processingMessage ? "Glass-box inference" : "Taxonomy output"}
          </p>
          <p className="mt-1 text-xs text-mercury-silver">
            {processingMessage ? "Sequential model trace" : "Meso and macro labels"}
          </p>
        </div>
        <StatusPill status={displayStatus} />
      </div>

      {status === "error" ? (
        <div className="rounded-lg border border-red-300/20 bg-red-400/10 p-4 text-sm text-red-100">
          {errorMessage}
        </div>
      ) : processingMessage ? (
        <ProcessingTrace
          message={processingMessage}
          stepIndex={processingStepIndex ?? 2}
        />
      ) : result && revealResult ? (
        <motion.div className="space-y-6" layout>
          <motion.div className="rounded-lg bg-mercury-graphite/80 p-4" layout>
            <p className="font-mono text-xs uppercase text-mercury-silver">
              Cosine Similarity (<MathText math="s^*" />)
            </p>
            <p className="mt-2 text-4xl font-normal text-mercury-starlight">
              {result.topSimilarity.toFixed(3)}
            </p>
            <p className="mt-2 text-sm leading-6 text-mercury-silver">
              Live embedding similarity to pre-computed taxonomy centroids.
            </p>
          </motion.div>

          <div>
            <p className="mb-1 font-mono text-xs uppercase text-mercury-silver">
              Meso
            </p>
            {result.meso.map((prediction) => (
              <TaxonomyBadge key={prediction.label} prediction={prediction} />
            ))}
          </div>

          <div>
            <p className="mb-1 font-mono text-xs uppercase text-mercury-silver">
              Macro
            </p>
            {result.macro.map((prediction) => (
              <TaxonomyBadge key={prediction.label} prediction={prediction} />
            ))}
          </div>
        </motion.div>
      ) : (
        <div className="flex min-h-80 flex-col items-center justify-center rounded-lg border border-dashed border-mercury-lead/30 text-center">
          <Activity className="mb-4 h-8 w-8 text-mercury-silver" />
          <p className="text-sm text-mercury-starlight">Awaiting inference</p>
        </div>
      )}
    </Card>
  );
}

function ProcessingTrace({
  message,
  stepIndex
}: {
  message: string;
  stepIndex: number;
}) {
  return (
    <motion.div
      layout
      className="flex min-h-80 flex-col justify-center rounded-lg border border-mercury-lead/30 bg-mercury-graphite/70 p-5"
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
    >
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-mercury-blue text-white">
          <Activity className="h-5 w-5" />
        </span>
        <div>
          <p className="font-mono text-xs uppercase text-mercury-silver">
            Inference trace
          </p>
          <motion.p
            className="mt-2 text-lg font-semibold leading-7 text-mercury-starlight"
            key={message}
            layout
          >
            {message}
          </motion.p>
        </div>
      </div>
      <div className="mt-8 grid gap-3">
        {[0, 1, 2].map((index) => (
          <div
            className="grid grid-cols-[42px_1fr] items-center gap-3"
            key={index}
          >
            <span className="font-mono text-xs text-mercury-silver">
              0{index + 1}
            </span>
            <span className="h-2 overflow-hidden rounded-full bg-apple-mist">
              <motion.span
                animate={{ width: index <= stepIndex ? "100%" : "0%" }}
                className="block h-full rounded-full bg-mercury-blue"
                transition={{ duration: 0.35, ease: "easeOut" }}
              />
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function StatusPill({ status }: { status: string }) {
  const ready = status === "success";
  const error = status === "error";

  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-mercury-ghost/10 px-3 py-1 text-xs text-mercury-starlight">
      {ready ? (
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />
      ) : error ? (
        <AlertCircle className="h-3.5 w-3.5 text-red-300" />
      ) : (
        <Activity className="h-3.5 w-3.5 text-mercury-silver" />
      )}
      {status}
    </span>
  );
}
