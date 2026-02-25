"use client";

import { useEffect } from "react";

import { AnalysisPanel } from "@/components/analysis/AnalysisPanel";
import { CoachingPanel } from "@/components/analysis/CoachingPanel";
import { BoardControls } from "@/components/board/BoardControls";
import { CapturedPieces } from "@/components/board/CapturedPieces";
import { ChessBoard } from "@/components/board/ChessBoard";
import { EvalBar } from "@/components/board/EvalBar";
import { MoveList } from "@/components/board/MoveList";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { useGameStore } from "@/stores/useGameStore";

export default function HomePage() {
  const fen = useGameStore((state) => state.fen);
  const moveHistory = useGameStore((state) => state.moveHistory);
  const currentMoveIndex = useGameStore((state) => state.currentMoveIndex);
  const loadPGN = useGameStore((state) => state.loadPGN);

  const analyzePosition = useAnalysisStore((state) => state.analyzePosition);
  const getCoaching = useAnalysisStore((state) => state.getCoaching);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);

  useEffect(() => {
    analyzePosition(fen).catch(() => undefined);
    // Run only once at initial load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const requestCoaching = async () => {
    if (!currentAnalysis) {
      return;
    }

    const lastMove = currentMoveIndex > 0 ? moveHistory[currentMoveIndex - 1]?.san : undefined;
    const userMove = currentMoveIndex >= 0 ? moveHistory[currentMoveIndex]?.san : undefined;

    await getCoaching({
      fen,
      last_move: lastMove,
      user_move: userMove,
      best_move: currentAnalysis.best_moves[0]?.san ?? currentAnalysis.best_moves[0]?.move ?? "",
      evaluation_before: currentAnalysis.evaluation.value,
      evaluation_after: currentAnalysis.evaluation.value,
      concepts: currentAnalysis.position_concepts,
      player_level: "intermediate",
    });
  };

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 md:px-6">
      <section className="rounded-xl border border-gray-800 bg-gray-900/70 p-6">
        <h1 className="text-3xl font-bold text-gray-100">ChessCoach AI</h1>
        <p className="mt-2 text-lg text-cyan-300">The chess engine that explains the why.</p>
        <p className="mt-2 text-gray-400">
          Play a move to get started or import a game for full review.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-[1.4fr_0.85fr] lg:grid-cols-[minmax(640px,1.7fr)_minmax(220px,0.75fr)_minmax(220px,0.75fr)]">
        <section className="space-y-3">
          <div className="grid grid-cols-[44px_1fr] gap-3">
            <div className="h-full min-h-[320px]">
              <EvalBar evaluation={currentAnalysis?.evaluation} />
            </div>
            <ChessBoard />
          </div>
          <BoardControls
            onImportPGN={(pgn) => {
              const ok = loadPGN(pgn);
              if (ok) {
                const nextFen = useGameStore.getState().fen;
                analyzePosition(nextFen).catch(() => undefined);
              }
            }}
          />
          <CapturedPieces />
          <MoveList />
        </section>

        <section className="space-y-4 lg:hidden">
          <AnalysisPanel />
          <CoachingPanel onRequestCoaching={() => requestCoaching().catch(() => undefined)} />
        </section>

        <section className="hidden lg:block">
          <AnalysisPanel />
        </section>

        <section className="hidden lg:block">
          <CoachingPanel onRequestCoaching={() => requestCoaching().catch(() => undefined)} />
        </section>
      </div>
    </main>
  );
}
