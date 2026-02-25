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
    <div className="relative h-full min-h-[320px] w-11 overflow-hidden rounded-lg border border-gray-700 bg-gradient-to-b from-gray-900 to-black">
      <div
        className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-gray-100 to-white transition-all duration-500 ease-out"
        style={{ height: `${whitePercent}%` }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="rounded bg-black/65 px-1.5 py-0.5 text-xs font-semibold text-gray-100">
          {formatEvaluation(evaluation)}
        </span>
      </div>
    </div>
  );
}
