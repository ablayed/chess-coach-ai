"use client";

import { Chess } from "chess.js";
import { FormEvent, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { parseLichessGameId } from "@/lib/chess-utils";
import type { ReviewRequest } from "@/types/api";

type ImportTab = "pgn" | "lichess";

interface GameImportProps {
  onSubmit: (payload: ReviewRequest) => Promise<void>;
  isLoading?: boolean;
}

export function GameImport({ onSubmit, isLoading = false }: GameImportProps) {
  const [tab, setTab] = useState<ImportTab>("pgn");
  const [pgn, setPgn] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    if (tab === "pgn") {
      return pgn.trim().length > 0;
    }
    return url.trim().length > 0;
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

      await onSubmit({ pgn, depth: 20, player_color: "white" });
      return;
    }

    const gameId = parseLichessGameId(url);
    if (!gameId) {
      setError("Invalid Lichess URL. Use formats like lichess.org/abcd1234.");
      return;
    }

    await onSubmit({ lichess_url: url, depth: 20, player_color: "white" });
  };

  return (
    <Card className="space-y-4">
      <div className="flex items-center gap-2">
        <Button variant={tab === "pgn" ? "primary" : "secondary"} size="sm" onClick={() => setTab("pgn")}>
          Paste PGN
        </Button>
        <Button
          variant={tab === "lichess" ? "primary" : "secondary"}
          size="sm"
          onClick={() => setTab("lichess")}
        >
          Lichess URL
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {tab === "pgn" ? (
          <textarea
            className="min-h-[160px] w-full rounded-md border border-gray-700 bg-gray-950 p-3 text-sm text-gray-100 outline-none focus:border-cyan-500"
            placeholder="Paste PGN here"
            value={pgn}
            onChange={(event) => setPgn(event.target.value)}
          />
        ) : (
          <Input
            placeholder="https://lichess.org/abcd1234"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
          />
        )}

        {error ? <p className="text-sm text-red-400">{error}</p> : null}

        <Button type="submit" disabled={!canSubmit || isLoading}>
          {isLoading ? "Importing..." : "Analyze Game"}
        </Button>
      </form>
    </Card>
  );
}
