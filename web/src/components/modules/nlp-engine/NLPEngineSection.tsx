"use client";

import { useEffect, useState } from "react";
import { FilingSnippetInput } from "@/components/modules/nlp-engine/FilingSnippetInput";
import { InferenceResultPanel } from "@/components/modules/nlp-engine/InferenceResultPanel";
import { SectionHeader } from "@/components/shell/SectionHeader";
import { MathText } from "@/components/ui/MathText";
import { useInferenceStore } from "@/stores/useInferenceStore";

const inferenceProcessingSteps = [
  "Step 1/3: Tokenizing Item 1A excerpt...",
  "Step 2/3: Extracting all-MiniLM-L6-v2 embeddings...",
  "Step 3/3: Computing cosine similarity against taxonomy centroids..."
] as const;

export function NLPEngineSection() {
  const status = useInferenceStore((state) => state.status);
  const lastRequestId = useInferenceStore((state) => state.lastRequestId);
  const [processingStepIndex, setProcessingStepIndex] = useState<number | null>(null);
  const [sequenceComplete, setSequenceComplete] = useState(false);

  useEffect(() => {
    if (!lastRequestId) {
      setProcessingStepIndex(null);
      setSequenceComplete(false);
      return;
    }

    setProcessingStepIndex(0);
    setSequenceComplete(false);

    const timers = [
      window.setTimeout(() => setProcessingStepIndex(1), 600),
      window.setTimeout(() => setProcessingStepIndex(2), 1400),
      window.setTimeout(() => {
        setProcessingStepIndex(null);
        setSequenceComplete(true);
      }, 2000)
    ];

    return () => timers.forEach((timer) => window.clearTimeout(timer));
  }, [lastRequestId]);

  useEffect(() => {
    if (status === "idle" || status === "error") {
      setProcessingStepIndex(null);
      setSequenceComplete(false);
    }
  }, [status]);

  const sequenceRunning =
    Boolean(lastRequestId) &&
    status !== "idle" &&
    status !== "error" &&
    !sequenceComplete;
  const networkStillLoading = status === "loading";
  const processingMessage =
    sequenceRunning || networkStillLoading
      ? inferenceProcessingSteps[processingStepIndex ?? 2]
      : null;
  const revealResult = status === "success" && sequenceComplete;

  return (
    <section
      className="min-h-[calc(100vh-4rem)] border-b border-mercury-lead/20 bg-white px-4 py-16 sm:px-6 lg:px-8"
      id="nlp"
    >
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <SectionHeader
              copy="Paste a risk-factor excerpt and score it against the pre-computed meso and macro taxonomy centroids."
              kicker="03 / Live NLP Inference"
              title="NLP risk engine"
            />
            <div className="mt-10">
              <FilingSnippetInput sequenceActive={Boolean(processingMessage)} />
            </div>
          </div>
          <InferenceResultPanel
            processingMessage={processingMessage}
            processingStepIndex={processingStepIndex}
            revealResult={revealResult}
          />
        </div>
        <div className="w-full flex justify-center py-4">
          <div className="thin-scrollbar max-w-full overflow-x-auto whitespace-nowrap rounded-full bg-apple-fog px-5 py-3 text-center text-2xl font-semibold text-apple-ink sm:text-3xl">
            <MathText math="s^* = \max_k \cos(\mathbf{e}_p, \mathbf{c}_k)" />
          </div>
        </div>
      </div>
    </section>
  );
}
