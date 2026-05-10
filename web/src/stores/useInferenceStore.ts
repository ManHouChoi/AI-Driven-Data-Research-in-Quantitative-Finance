"use client";

import { create } from "zustand";
import { classifyRisk } from "@/lib/api/classifyRisk";
import type {
  InferenceStatus,
  RiskClassificationResult
} from "@/types/inference";

interface LiveInferenceState {
  inputText: string;
  status: InferenceStatus;
  result: RiskClassificationResult | null;
  errorMessage: string | null;
  lastRequestId: string | null;
  setInputText: (text: string) => void;
  classifyText: () => Promise<void>;
  resetInference: () => void;
}

const defaultSnippet =
  "Our integrated resort operations are highly susceptible to global travel restrictions, infectious disease outbreaks, and cross-border quarantine mandates. Furthermore, our gaming revenues rely entirely on maintaining compliance with Macau SAR government concessions and navigating intense resort competition.";

export const useInferenceStore = create<LiveInferenceState>((set, get) => ({
  inputText: defaultSnippet,
  status: "idle",
  result: null,
  errorMessage: null,
  lastRequestId: null,
  setInputText: (inputText) => set({ inputText }),
  classifyText: async () => {
    const text = get().inputText.trim();

    if (!text) {
      set({
        status: "error",
        errorMessage: "Enter a filing excerpt before running inference."
      });
      return;
    }

    const requestId = crypto.randomUUID();
    set({
      status: "loading",
      errorMessage: null,
      lastRequestId: requestId
    });

    try {
      const response = await classifyRisk({ text });

      if (get().lastRequestId !== requestId) {
        return;
      }

      set({
        status: "success",
        result: response,
        errorMessage: null
      });
    } catch (error) {
      if (get().lastRequestId !== requestId) {
        return;
      }

      set({
        status: "error",
        errorMessage:
          error instanceof Error ? error.message : "Risk classification failed"
      });
    }
  },
  resetInference: () =>
    set({
      inputText: defaultSnippet,
      status: "idle",
      result: null,
      errorMessage: null,
      lastRequestId: null
    })
}));
