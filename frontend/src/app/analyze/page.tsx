"use client";

import { FormEvent, useState } from "react";

import { AnalysisPanel } from "@/components/analysis/AnalysisPanel";
import { CoachingPanel } from "@/components/analysis/CoachingPanel";
import { BoardControls } from "@/components/board/BoardControls";
import { CapturedPieces } from "@/components/board/CapturedPieces";
import { ChessBoard } from "@/components/board/ChessBoard";
import { EvalBar } from "@/components/board/EvalBar";
import { MoveList } from "@/components/board/MoveList";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { useGameStore } from "@/stores/useGameStore";

export default function AnalyzePage() {
  const fen = useGameStore((state) => state.fen);
  const setFEN = useGameStore((state) => state.setFEN);
  const loadPGN = useGameStore((state) => state.loadPGN);
  const moveHistory = useGameStore((state) => state.moveHistory);
  const currentMoveIndex = useGameStore((state) => state.currentMoveIndex);

  const analyzePosition = useAnalysisStore((state) => state.analyzePosition);
  const getCoaching = useAnalysisStore((state) => state.getCoaching);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);

  const [fenInput, setFenInput] = useState(fen);
  const [fenError, setFenError] = useState<string | null>(null);

  const handleSubmitFen = (event: FormEvent) => {
    event.preventDefault();
    setFenError(null);
    const ok = setFEN(fenInput);
    if (!ok) {
      setFenError("Invalid FEN string.");
      return;
    }
    const nextFen = useGameStore.getState().fen;
    analyzePosition(nextFen).catch(() => undefined);
  };

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
      <h1 className="text-2xl font-semibold text-gray-100">Analyze Any Position</h1>

      <form onSubmit={handleSubmitFen} className="space-y-2 rounded-xl border border-gray-700 bg-gray-800/60 p-4">
        <label htmlFor="fen-input" className="text-sm text-gray-300">
          Paste FEN
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            id="fen-input"
            value={fenInput}
            onChange={(event) => setFenInput(event.target.value)}
            placeholder="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
          />
          <Button type="submit">Load</Button>
        </div>
        {fenError ? <p className="text-sm text-red-400">{fenError}</p> : null}
      </form>

      <div className="grid gap-4 lg:grid-cols-[56px_minmax(280px,620px)_minmax(260px,1fr)_minmax(260px,1fr)]">
        <div className="h-[320px] md:h-[620px]">
          <EvalBar evaluation={currentAnalysis?.evaluation} />
        </div>

        <section className="space-y-3">
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

        <section>
          <AnalysisPanel />
        </section>

        <section>
          <CoachingPanel onRequestCoaching={() => requestCoaching().catch(() => undefined)} />
        </section>
      </div>
    </main>
  );
}
