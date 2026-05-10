"use client";

import { useAttentionMatrix } from "@/lib/data/loadAttentionMatrix";
import { useDashboardStore } from "@/stores/useDashboardStore";
import { Select } from "@/components/ui/Select";

export function FirmSelector() {
  const { data } = useAttentionMatrix();
  const firms = data?.firms ?? [];
  const selectedFirmId = useDashboardStore((state) => state.graph.selectedFirmId);
  const comparisonFirmId = useDashboardStore(
    (state) => state.graph.comparisonFirmId
  );
  const setSelectedFirmId = useDashboardStore((state) => state.setSelectedFirmId);
  const setComparisonFirmId = useDashboardStore(
    (state) => state.setComparisonFirmId
  );

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <label>
        <span className="mb-2 block text-xs text-mercury-silver">
          Source firm
        </span>
        <Select
          className="w-full"
          disabled={!data}
          value={selectedFirmId ?? ""}
          onChange={(event) => setSelectedFirmId(event.target.value || null)}
        >
          {firms.map((firm) => (
            <option key={firm.id} value={firm.id}>
              {firm.ticker} · {firm.sector}
            </option>
          ))}
        </Select>
      </label>

      <label>
        <span className="mb-2 block text-xs text-mercury-silver">
          Target focus
        </span>
        <Select
          className="w-full"
          disabled={!data}
          value={comparisonFirmId ?? ""}
          onChange={(event) =>
            setComparisonFirmId(event.target.value || null)
          }
        >
          <option value="">Highest attention</option>
          {firms.map((firm) => (
            <option key={firm.id} value={firm.id}>
              {firm.ticker} · {firm.sector}
            </option>
          ))}
        </Select>
      </label>
    </div>
  );
}
