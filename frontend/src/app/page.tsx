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
    <main className="mx-auto max-w-[1600px] space-y-4 px-4 py-4 md:px-6 md:py-6">
      <h1 className="text-2xl font-semibold text-gray-100">The chess engine that explains the why.</h1>

      <div className="grid gap-4 lg:grid-cols-[56px_minmax(280px,620px)_minmax(260px,1fr)_minmax(260px,1fr)]">
        <div className="order-2 h-[320px] md:h-[620px] lg:order-1">
          <EvalBar evaluation={currentAnalysis?.evaluation} />
        </div>

        <section className="order-1 space-y-3 lg:order-2">
          <ChessBoard />
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

        <section className="order-3">
          <AnalysisPanel />
        </section>

        <section className="order-4">
          <CoachingPanel onRequestCoaching={() => requestCoaching().catch(() => undefined)} />
        </section>
      </div>
    </main>
  );
}
