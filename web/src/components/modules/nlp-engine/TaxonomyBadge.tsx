import clsx from "clsx";
import type { TaxonomyPrediction } from "@/types/inference";

interface TaxonomyBadgeProps {
  prediction: TaxonomyPrediction;
}

export function TaxonomyBadge({ prediction }: TaxonomyBadgeProps) {
  const confidence = Math.max(0, Math.min(100, prediction.similarity * 100));

  return (
    <div
      className={clsx(
        "flex items-center justify-between gap-4 border-b border-mercury-lead/20 py-4 last:border-b-0",
        prediction.level === "macro" && "border-mercury-ghost/20"
      )}
    >
      <div>
        <p className="text-sm font-medium text-mercury-starlight">
          {prediction.label}
        </p>
        <p className="mt-1 font-mono text-xs uppercase text-mercury-silver">
          {prediction.level}
        </p>
      </div>
      <div className="min-w-28 text-right">
        <span className="rounded-full bg-mercury-ghost/10 px-3 py-1 font-mono text-xs text-mercury-starlight">
          {confidence.toFixed(1)}%
        </span>
        <span className="mt-2 block h-1.5 overflow-hidden rounded-full bg-apple-mist">
          <span
            className="block h-full rounded-full bg-mercury-blue"
            style={{ width: `${confidence}%` }}
          />
        </span>
      </div>
    </div>
  );
}
