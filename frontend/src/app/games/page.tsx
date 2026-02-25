"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/useAuthStore";
import type { GameListItem } from "@/types/api";

function formatDate(input: string): string {
  const date = new Date(input);
  if (Number.isNaN(date.getTime())) {
    return input;
  }
  return date.toLocaleString();
}

export default function GamesPage() {
  const user = useAuthStore((state) => state.user);

  const [games, setGames] = useState<GameListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      return;
    }

    setIsLoading(true);
    setError(null);

    api
      .get<GameListItem[]>("/api/v1/games")
      .then((response) => setGames(response))
      .catch((err: unknown) => {
        const message = err instanceof ApiError ? err.detail : "Failed to load saved games";
        setError(message);
      })
      .finally(() => setIsLoading(false));
  }, [user]);

  if (!user) {
    return (
      <main className="mx-auto max-w-4xl space-y-3 px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-100">Saved Games</h1>
        <p className="text-gray-300">Sign in to access your saved reviews.</p>
        <Link href="/auth/login" className="text-cyan-300 underline">
          Go to login
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-100">Saved Games</h1>

      {isLoading ? (
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-6 text-gray-300">Loading games...</div>
      ) : null}

      {error ? (
        <div className="mb-4 rounded-lg border border-red-500 bg-red-900/30 p-4">
          <p className="text-red-300">{error}</p>
        </div>
      ) : null}

      {!isLoading && games.length === 0 ? (
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-6 text-gray-400">No saved games yet.</div>
      ) : null}

      <div className="space-y-3">
        {games.map((game) => (
          <Link
            key={game.id}
            href={`/review?gameId=${game.id}`}
            className="block rounded-lg border border-gray-700 bg-gray-800 p-4 transition hover:border-cyan-500/60"
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="font-semibold text-gray-100">
                  {game.white_player ?? "White"} vs {game.black_player ?? "Black"}
                </p>
                <p className="mt-1 text-sm text-gray-400">{formatDate(game.created_at)}</p>
              </div>
              <div className="text-right">
                {game.accuracy !== null && game.accuracy !== undefined ? (
                  <p className="text-sm text-cyan-300">Accuracy {game.accuracy.toFixed(1)}%</p>
                ) : null}
                <p className="text-xs text-gray-500">{game.result ?? "-"}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
