"use client";

import type { ReviewSummary } from "@/types/api";

interface GameSummaryProps {
  summary: ReviewSummary | null;
}

export function GameSummary({ summary }: GameSummaryProps) {
  if (!summary) {
    return null;
  }

  const classColors: Record<string, string> = {
    brilliant: "bg-cyan-500",
    great: "bg-green-500",
    good: "bg-green-400",
    inaccuracy: "bg-yellow-500",
    mistake: "bg-orange-500",
    blunder: "bg-red-500",
  };

  return (
    <div className="mb-6 rounded-lg border border-gray-700 bg-gray-800 p-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="text-center">
          <div className="text-4xl font-bold text-cyan-400">{summary.accuracy.toFixed(1)}%</div>
          <div className="mt-1 text-sm text-gray-400">Accuracy</div>
        </div>

        <div>
          <h3 className="mb-2 text-sm font-bold text-gray-400">Move Breakdown</h3>
          <div className="space-y-1">
            {Object.entries(summary.move_classifications).map(([type, count]) =>
              count > 0 ? (
                <div key={type} className="flex items-center gap-2">
                  <span className={`h-3 w-3 rounded-full ${classColors[type] ?? "bg-gray-500"}`} />
                  <span className="text-sm capitalize text-gray-300">{type}</span>
                  <span className="ml-auto text-sm text-gray-500">{count}</span>
                </div>
              ) : null,
            )}
          </div>
        </div>

        <div>
          <h3 className="mb-2 text-sm font-bold text-gray-400">Focus Areas</h3>
          <div className="flex flex-wrap gap-2">
            {summary.themes_to_improve.map((theme) => (
              <span key={theme} className="rounded bg-gray-700 px-2 py-1 text-xs text-gray-300">
                {theme.replaceAll("_", " ")}
              </span>
            ))}
          </div>
        </div>
      </div>

      {summary.overall_coaching ? (
        <div className="mt-4 border-t border-gray-700 pt-4">
          <p className="text-sm leading-relaxed text-gray-300">{summary.overall_coaching}</p>
        </div>
      ) : null}
    </div>
  );
}
