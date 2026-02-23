"use client";

import { useMemo } from "react";

import { Card } from "@/components/ui/Card";
import { MOVE_CLASS_COLORS } from "@/lib/constants";
import type { ReviewSummary } from "@/types/api";

interface GameSummaryProps {
  summary: ReviewSummary;
}

export function GameSummary({ summary }: GameSummaryProps) {
  const ringStyle = useMemo(
    () => ({
      background: `conic-gradient(#06b6d4 ${summary.accuracy}%, #1f2937 ${summary.accuracy}% 100%)`,
    }),
    [summary.accuracy],
  );

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative h-24 w-24 rounded-full p-2" style={ringStyle}>
          <div className="flex h-full w-full items-center justify-center rounded-full bg-gray-900 text-lg font-bold text-gray-100">
            {summary.accuracy.toFixed(1)}%
          </div>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-100">Game Summary</h2>
          <p className="text-sm text-gray-400">Your overall move quality and key improvement themes.</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400">
              <th className="py-2">Classification</th>
              <th className="py-2">Count</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(summary.move_classifications).map(([name, count]) => (
              <tr key={name} className="border-b border-gray-800">
                <td className="py-2">
                  <span className="inline-flex items-center gap-2">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: MOVE_CLASS_COLORS[name] ?? "#9ca3af" }}
                    />
                    {name}
                  </span>
                </td>
                <td className="py-2 text-gray-200">{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap gap-2">
        {summary.themes_to_improve.map((theme) => (
          <button
            key={theme}
            type="button"
            className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200"
          >
            {theme}
          </button>
        ))}
      </div>

      <p className="text-sm leading-relaxed text-gray-200">{summary.overall_coaching}</p>
    </Card>
  );
}
