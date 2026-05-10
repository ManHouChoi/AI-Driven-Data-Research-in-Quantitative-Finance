"use client";

import { RotateCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useInferenceStore } from "@/stores/useInferenceStore";

interface FilingSnippetInputProps {
  sequenceActive?: boolean;
}

export function FilingSnippetInput({
  sequenceActive = false
}: FilingSnippetInputProps) {
  const inputText = useInferenceStore((state) => state.inputText);
  const status = useInferenceStore((state) => state.status);
  const setInputText = useInferenceStore((state) => state.setInputText);
  const classifyText = useInferenceStore((state) => state.classifyText);
  const resetInference = useInferenceStore((state) => state.resetInference);
  const loading = status === "loading" || sequenceActive;

  return (
    <div className="flex h-full flex-col">
      <label className="mb-3 text-sm font-medium text-mercury-starlight">
        Item 1A excerpt
      </label>
      <textarea
        className="min-h-72 flex-1 resize-none rounded-lg border border-mercury-lead/24 bg-mercury-graphite p-5 text-base leading-7 text-mercury-starlight outline-none transition placeholder:text-mercury-silver/60 focus:border-mercury-ghost/50"
        value={inputText}
        onChange={(event) => setInputText(event.target.value)}
      />
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <Button
          disabled={loading}
          icon={loading ? <Spinner /> : <Sparkles className="h-4 w-4" />}
          variant="primary"
          onClick={() => void classifyText()}
        >
          {loading ? "Processing" : "Run Inference"}
        </Button>
        <Button
          disabled={loading}
          icon={<RotateCcw className="h-4 w-4" />}
          variant="secondary"
          onClick={resetInference}
        >
          Reset
        </Button>
      </div>
    </div>
  );
}
