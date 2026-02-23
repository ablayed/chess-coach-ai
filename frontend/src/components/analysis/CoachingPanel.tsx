"use client";

import { MoveClassBadge } from "@/components/analysis/MoveClassBadge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Loading } from "@/components/ui/Loading";
import { useAnalysisStore } from "@/stores/useAnalysisStore";

interface CoachingPanelProps {
  onRequestCoaching: () => void;
}

export function CoachingPanel({ onRequestCoaching }: CoachingPanelProps) {
  const coaching = useAnalysisStore((state) => state.coaching);
  const isLoadingCoaching = useAnalysisStore((state) => state.isLoadingCoaching);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);

  return (
    <Card className="h-full space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-100">Coaching</h2>
        <Button
          size="sm"
          onClick={onRequestCoaching}
          disabled={!currentAnalysis || isLoadingCoaching}
          variant="primary"
        >
          Get Coaching
        </Button>
      </div>

      {isLoadingCoaching ? <Loading label="Generating explanation..." /> : null}

      {!coaching && !isLoadingCoaching ? (
        <p className="text-sm text-gray-400">Request coaching to get a natural-language explanation of the position.</p>
      ) : null}

      {coaching ? (
        <div className="space-y-4">
          <MoveClassBadge classification={coaching.move_classification} />
          <p className="text-sm leading-relaxed text-gray-200">{coaching.explanation}</p>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-gray-300">Book references</h3>
            <div className="space-y-2">
              {coaching.book_references.map((ref) => (
                <div key={`${ref.source}-${ref.relevance_score}`} className="rounded-md border border-gray-700 bg-gray-900/40 p-2">
                  <p className="text-xs font-semibold text-cyan-200">{ref.source}</p>
                  <p className="text-xs text-gray-300">{ref.passage_summary}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </Card>
  );
}
