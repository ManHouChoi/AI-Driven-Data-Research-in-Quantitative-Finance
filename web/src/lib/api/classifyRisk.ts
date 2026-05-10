import type {
  ClassifyRiskRequest,
  ClassifyRiskResponse
} from "@/types/inference";

export async function classifyRisk(
  payload: ClassifyRiskRequest
): Promise<ClassifyRiskResponse> {
  const response = await fetch("/api/classify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Risk classification failed");
  }

  return response.json() as Promise<ClassifyRiskResponse>;
}
