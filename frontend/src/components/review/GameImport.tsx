"use client";

import { Chess } from "chess.js";
import { FormEvent, useMemo, useState } from "react";

import clsx from "clsx";

import { parseLichessGameId } from "@/lib/chess-utils";
import type { ReviewRequest } from "@/types/api";

type ImportTab = "pgn" | "lichess";

interface GameImportProps {
  onSubmit: (payload: ReviewRequest) => Promise<void>;
  isLoading?: boolean;
  onEstimatedMoves?: (totalMoves: number | null) => void;
}

export function GameImport({ onSubmit, isLoading = false, onEstimatedMoves }: GameImportProps) {
  const [tab, setTab] = useState<ImportTab>("pgn");
  const [pgn, setPgn] = useState("");
  const [url, setUrl] = useState("");
  const [playerColor, setPlayerColor] = useState<"white" | "black">("white");
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    if (tab === "pgn") {
      return pgn.trim().length > 5;
    }
    return Boolean(parseLichessGameId(url));
  }, [pgn, tab, url]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (tab === "pgn") {
      const board = new Chess();
      try {
        board.loadPgn(pgn);
      } catch {
        setError("Invalid PGN format. Please paste a valid PGN.");
        return;
      }

      onEstimatedMoves?.(board.history().length);
      await onSubmit({ pgn: pgn.trim(), depth: 18, player_color: playerColor });
      return;
    }

    const gameId = parseLichessGameId(url);
    if (!gameId) {
      setError("Invalid Lichess URL. Use formats like lichess.org/abcd1234.");
      return;
    }

    onEstimatedMoves?.(null);
    await onSubmit({ lichess_url: url.trim(), depth: 18, player_color: playerColor });
  };

  return (
    <div className="mx-auto w-full max-w-2xl rounded-xl border border-gray-700 bg-gray-800 p-5">
      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={() => setTab("pgn")}
          className={clsx(
            "rounded-lg px-4 py-2 text-sm font-medium transition",
            tab === "pgn" ? "bg-cyan-600 text-white" : "bg-gray-900 text-gray-400 hover:bg-gray-700",
          )}
        >
          Paste PGN
        </button>
        <button
          type="button"
          onClick={() => setTab("lichess")}
          className={clsx(
            "rounded-lg px-4 py-2 text-sm font-medium transition",
            tab === "lichess" ? "bg-cyan-600 text-white" : "bg-gray-900 text-gray-400 hover:bg-gray-700",
          )}
        >
          Lichess URL
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {tab === "pgn" ? (
          <textarea
            className="h-48 w-full resize-none rounded-lg border border-gray-700 bg-gray-900 p-4 font-mono text-sm text-gray-200 focus:border-cyan-500 focus:outline-none"
            placeholder={"Paste your PGN here...\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6..."}
            value={pgn}
            onChange={(event) => setPgn(event.target.value)}
          />
        ) : (
          <input
            type="text"
            className="w-full rounded-lg border border-gray-700 bg-gray-900 p-4 text-gray-200 focus:border-cyan-500 focus:outline-none"
            placeholder="https://lichess.org/abcd1234"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
          />
        )}

        <div className="mt-2 flex items-center gap-4">
          <span className="text-sm text-gray-400">I played as:</span>
          <button
            type="button"
            onClick={() => setPlayerColor("white")}
            className={clsx(
              "rounded px-3 py-1.5 text-sm",
              playerColor === "white" ? "bg-white font-bold text-gray-900" : "bg-gray-700 text-gray-400",
            )}
          >
            White
          </button>
          <button
            type="button"
            onClick={() => setPlayerColor("black")}
            className={clsx(
              "rounded px-3 py-1.5 text-sm",
              playerColor === "black"
                ? "border border-white bg-gray-900 font-bold text-white"
                : "bg-gray-700 text-gray-400",
            )}
          >
            Black
          </button>
        </div>

        {error ? <p className="text-sm text-red-400">{error}</p> : null}

        <button
          type="submit"
          disabled={!canSubmit || isLoading}
          className="mt-4 w-full rounded-lg bg-cyan-600 py-3 font-bold text-white transition hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500"
        >
          {isLoading ? "Analyzing..." : "Analyze Game"}
        </button>
      </form>
    </div>
  );
}
