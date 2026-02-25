"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { GameImport } from "@/components/review/GameImport";
import { GameSummary } from "@/components/review/GameSummary";
import { ReviewBoard } from "@/components/review/ReviewBoard";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/useAuthStore";
import type { GameDetail, ReviewRequest, ReviewResponse, SaveGameRequest } from "@/types/api";

function ReviewPageContent() {
  const searchParams = useSearchParams();
  const [reviewData, setReviewData] = useState<ReviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [playerColor, setPlayerColor] = useState<"white" | "black">("white");
  const [lastPayload, setLastPayload] = useState<ReviewRequest | null>(null);
  const [estimatedMoves, setEstimatedMoves] = useState<number | null>(null);
  const [progressMove, setProgressMove] = useState(1);
  const [isSaving, setIsSaving] = useState(false);
  const [savedGameId, setSavedGameId] = useState<string | null>(null);

  const user = useAuthStore((state) => state.user);

  useEffect(() => {
    if (!isLoading) {
      return;
    }

    const id = setInterval(() => {
      setProgressMove((prev) => {
        if (estimatedMoves) {
          return Math.min(prev + 1, Math.max(estimatedMoves, 1));
        }
        return prev + 1;
      });
    }, 900);

    return () => clearInterval(id);
  }, [estimatedMoves, isLoading]);

  useEffect(() => {
    const gameId = searchParams.get("gameId");
    if (!gameId) {
      return;
    }

    setIsLoading(true);
    setError(null);
    api
      .get<ReviewResponse>(`/api/v1/review/${gameId}`)
      .then((response) => {
        setReviewData(response);
        setSavedGameId(response.game_id);
        setPlayerColor(response.player_color ?? "white");
      })
      .catch((err: unknown) => {
        const message = err instanceof ApiError ? err.detail : "Failed to load saved review";
        setError(message);
      })
      .finally(() => setIsLoading(false));
  }, [searchParams]);

  const handleImport = async (payload: ReviewRequest) => {
    setIsLoading(true);
    setError(null);
    setSavedGameId(null);
    setProgressMove(1);
    setLastPayload(payload);
    setPlayerColor(payload.player_color ?? "white");

    try {
      const response = await api.post<ReviewResponse>("/api/v1/review/game", payload);
      setReviewData(response);
      if (response.status === "saved") {
        setSavedGameId(response.game_id);
      }
    } catch (err: unknown) {
      const message = err instanceof ApiError ? err.detail : "Failed to review game";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!reviewData || !reviewData.pgn || !lastPayload || isSaving || !user) {
      return;
    }

    const payload: SaveGameRequest = {
      pgn: reviewData.pgn,
      lichess_url: lastPayload.lichess_url,
      player_color: playerColor,
      summary: reviewData.summary,
      moves: reviewData.moves,
    };

    setIsSaving(true);
    setError(null);
    try {
      const saved = await api.post<GameDetail>("/api/v1/games", payload);
      setSavedGameId(saved.id);
    } catch (err: unknown) {
      const message = err instanceof ApiError ? err.detail : "Failed to save game";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-100">Game Review</h1>

      {!reviewData && !isLoading ? (
        <GameImport
          onSubmit={handleImport}
          isLoading={isLoading}
          onEstimatedMoves={(count) => setEstimatedMoves(count)}
        />
      ) : null}

      {isLoading ? (
        <div className="py-20 text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent" />
          <p className="text-gray-300">
            Analyzing move {progressMove}
            {estimatedMoves ? ` of ${estimatedMoves}` : ""}...
          </p>
          <p className="mt-2 text-sm text-gray-500">This can take 30-60 seconds on full games.</p>
        </div>
      ) : null}

      {error ? (
        <div className="mb-6 rounded-lg border border-red-500 bg-red-900/30 p-4">
          <p className="text-red-300">{error}</p>
          <button
            type="button"
            onClick={() => {
              setError(null);
              setReviewData(null);
              setSavedGameId(null);
            }}
            className="mt-2 text-sm text-red-200 underline"
          >
            Try again
          </button>
        </div>
      ) : null}

      {reviewData ? (
        <>
          <GameSummary summary={reviewData.summary} />
          <ReviewBoard moves={reviewData.moves} playerColor={playerColor} />

          <div className="mt-4 flex flex-wrap items-center gap-3">
            {user && !savedGameId ? (
              <button
                type="button"
                onClick={() => void handleSave()}
                disabled={isSaving || !lastPayload}
                className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500"
              >
                {isSaving ? "Saving..." : "Save Analysis"}
              </button>
            ) : null}

            {savedGameId ? (
              <Link href={`/review?gameId=${savedGameId}`} className="text-sm text-cyan-300 underline">
                Saved review #{savedGameId.slice(0, 8)}
              </Link>
            ) : null}

            <button
              type="button"
              onClick={() => {
                setReviewData(null);
                setSavedGameId(null);
                setLastPayload(null);
                setEstimatedMoves(null);
                setProgressMove(1);
              }}
              className="text-sm text-gray-400 underline"
            >
              Review another game
            </button>
          </div>
        </>
      ) : null}
    </main>
  );
}

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto max-w-7xl px-4 py-8">
          <div className="rounded-lg border border-gray-700 bg-gray-800 p-6 text-gray-300">Loading review page...</div>
        </main>
      }
    >
      <ReviewPageContent />
    </Suspense>
  );
}
