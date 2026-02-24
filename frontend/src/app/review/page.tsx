"use client";

import { useMemo, useState } from "react";

import { GameImport } from "@/components/review/GameImport";
import { GameSummary } from "@/components/review/GameSummary";
import { ReviewNav } from "@/components/review/ReviewNav";
import { ChessBoard } from "@/components/board/ChessBoard";
import { MoveList } from "@/components/board/MoveList";
import { Card } from "@/components/ui/Card";
import { api, ApiError } from "@/lib/api";
import { useGameStore } from "@/stores/useGameStore";
import type { ReviewRequest, ReviewResponse } from "@/types/api";

export default function ReviewPage() {
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentMoveIndex = useGameStore((state) => state.currentMoveIndex);
  const goBack = useGameStore((state) => state.goBack);
  const goForward = useGameStore((state) => state.goForward);
  const goToMove = useGameStore((state) => state.goToMove);
  const loadMovesFromSan = useGameStore((state) => state.loadMovesFromSan);

  const classificationMap = useMemo(() => {
    if (!review) {
      return {};
    }
    return review.moves.reduce<Record<number, string>>((acc, move) => {
      acc[move.move_number] = move.classification;
      return acc;
    }, {});
  }, [review]);

  const selectedMove = review?.moves[Math.max(currentMoveIndex, 0)] ?? null;

  const handleImport = async (payload: ReviewRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post<ReviewResponse>("/api/v1/review/game", payload);
      setReview(response);

      const sanMoves = response.moves.map((move) => move.move);
      loadMovesFromSan(sanMoves);
      goToMove(0);
    } catch (err: unknown) {
      const message = err instanceof ApiError ? err.detail : "Failed to review game";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-[1600px] space-y-4 px-4 py-4 md:px-6 md:py-6">
      <h1 className="text-2xl font-semibold text-gray-100">Game Review</h1>
      <GameImport onSubmit={handleImport} isLoading={loading} />

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      {review ? (
        <>
          {review.summary ? <GameSummary summary={review.summary} /> : null}

          <div className="grid gap-4 lg:grid-cols-[minmax(280px,620px)_minmax(260px,1fr)_minmax(260px,1fr)]">
            <section className="space-y-3">
              <ChessBoard interactive={false} bestMoveOverride={selectedMove?.best_move ?? null} />
              <ReviewNav
                currentMove={Math.max(currentMoveIndex, 0)}
                totalMoves={review.moves.length}
                onFirst={() => goToMove(0)}
                onBack={goBack}
                onForward={goForward}
                onLast={() => goToMove(review.moves.length - 1)}
              />
              <MoveList classifications={classificationMap} />
            </section>

            <Card className="space-y-3">
              <h2 className="text-lg font-semibold text-gray-100">Move Analysis</h2>
              {selectedMove ? (
                <div className="space-y-2 text-sm text-gray-200">
                  <p>
                    Move {selectedMove.move_number}: <span className="font-semibold">{selectedMove.move}</span>
                  </p>
                  <p>Best move: {selectedMove.best_move}</p>
                  <p>
                    Eval: {selectedMove.evaluation_before.toFixed(1)} {"->"} {selectedMove.evaluation_after.toFixed(1)}
                  </p>
                  <p>Classification: {selectedMove.classification}</p>
                  <p>Critical: {selectedMove.is_critical ? "Yes" : "No"}</p>
                </div>
              ) : (
                <p className="text-sm text-gray-400">Select a move from the list.</p>
              )}
            </Card>

            <Card className="space-y-3">
              <h2 className="text-lg font-semibold text-gray-100">Coaching Note</h2>
              {selectedMove?.coaching ? (
                <p className="text-sm leading-relaxed text-gray-200">{selectedMove.coaching}</p>
              ) : (
                <p className="text-sm text-gray-400">No coaching note for this move. Critical mistakes include coaching.</p>
              )}
            </Card>
          </div>
        </>
      ) : null}
    </main>
  );
}
