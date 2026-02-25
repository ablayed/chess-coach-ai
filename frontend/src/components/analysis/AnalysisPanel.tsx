"use client";

import { Card } from "@/components/ui/Card";
import { formatEvaluation } from "@/lib/chess-utils";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { useGameStore } from "@/stores/useGameStore";

export function AnalysisPanel() {
  const isAnalyzing = useAnalysisStore((state) => state.isAnalyzing);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);
  const streamingDepth = useAnalysisStore((state) => state.streamingDepth);
  const error = useAnalysisStore((state) => state.error);
  const analyzePosition = useAnalysisStore((state) => state.analyzePosition);
  const fen = useGameStore((state) => state.fen);

  return (
    <Card className="h-full space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-100">Engine Analysis</h2>
        <span className="text-xs uppercase tracking-wide text-gray-400">depth {streamingDepth || 0}/20</span>
      </div>

      {isAnalyzing ? (
        <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 p-3 text-sm text-cyan-200">
          <p className="animate-pulse">Analyzing... Depth {streamingDepth || 1}/20</p>
        </div>
      ) : null}
      {error ? (
        <div className="rounded-lg border border-red-500 bg-red-900/30 p-3">
          <p className="text-sm text-red-300">{error}</p>
          <button
            type="button"
            onClick={() => {
              analyzePosition(fen).catch(() => undefined);
            }}
            className="mt-2 text-xs text-red-200 underline"
          >
            Retry analysis
          </button>
        </div>
      ) : null}

      {currentAnalysis ? (
        <>
          <div className="rounded-lg border border-gray-700 bg-gray-900/60 p-3">
            <p className="text-xs uppercase text-gray-400">Evaluation</p>
            <p className="text-2xl font-bold text-cyan-300">{formatEvaluation(currentAnalysis.evaluation)}</p>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-300">Top lines</h3>
            {currentAnalysis.best_moves.slice(0, 3).map((line, idx) => (
              <div key={`${line.move}-${idx}`} className="rounded-md border border-gray-700 bg-gray-900/40 p-2 text-sm">
                <p className="font-semibold text-gray-100">
                  {idx + 1}. {line.san} ({formatEvaluation(line.evaluation)})
                </p>
                <p className="mt-1 text-xs text-gray-400">{line.pv_san.join(" ")}</p>
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-300">Position concepts</h3>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-md bg-gray-700 px-2 py-1 text-xs text-gray-100">
                {currentAnalysis.position_concepts.phase}
              </span>
              {currentAnalysis.position_concepts.tactical_motifs.map((motif) => (
                <span key={motif} className="rounded-md bg-gray-700 px-2 py-1 text-xs text-gray-200">
                  {motif}
                </span>
              ))}
              {currentAnalysis.position_concepts.strategic_themes.map((theme) => (
                <span key={theme} className="rounded-md bg-gray-700 px-2 py-1 text-xs text-gray-200">
                  {theme}
                </span>
              ))}
            </div>
          </div>
        </>
      ) : (
        <p className="text-sm text-gray-400">Make a move to begin analysis.</p>
      )}
    </Card>
  );
}
