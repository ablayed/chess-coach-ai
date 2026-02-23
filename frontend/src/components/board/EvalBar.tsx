"use client";

import { useMemo } from "react";

import { formatEvaluation, normalizeEvalToWhiteCp, sigmoidFromCp } from "@/lib/chess-utils";
import type { Evaluation } from "@/types/api";

interface EvalBarProps {
  evaluation: Evaluation | null | undefined;
}

export function EvalBar({ evaluation }: EvalBarProps) {
  const cp = useMemo(() => {
    if (!evaluation) {
      return 0;
    }
    return normalizeEvalToWhiteCp(evaluation);
  }, [evaluation]);

  const whiteRatio = sigmoidFromCp(cp);
  const whitePercent = Math.max(2, Math.min(98, whiteRatio * 100));

  return (
    <div className="relative h-full min-h-[320px] w-12 overflow-hidden rounded-lg border border-gray-700 bg-gray-950">
      <div
        className="absolute bottom-0 left-0 right-0 bg-gray-100 transition-all duration-500"
        style={{ height: `${whitePercent}%` }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="rounded bg-black/60 px-1.5 py-0.5 text-xs font-semibold text-gray-100">
          {formatEvaluation(evaluation)}
        </span>
      </div>
    </div>
  );
}
