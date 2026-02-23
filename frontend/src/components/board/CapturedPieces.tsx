"use client";

import { useMemo } from "react";

import { Card } from "@/components/ui/Card";
import { getCapturedPieces } from "@/lib/chess-utils";
import { useGameStore } from "@/stores/useGameStore";

export function CapturedPieces() {
  const chess = useGameStore((state) => state.chess);

  const captured = useMemo(() => getCapturedPieces(chess), [chess]);

  return (
    <Card className="space-y-3">
      <div>
        <p className="text-xs uppercase tracking-wide text-gray-400">Captured by White</p>
        <p className="mt-1 min-h-6 text-xl leading-6 text-gray-100">{captured.black.join(" ") || "-"}</p>
      </div>
      <div>
        <p className="text-xs uppercase tracking-wide text-gray-400">Captured by Black</p>
        <p className="mt-1 min-h-6 text-xl leading-6 text-gray-100">{captured.white.join(" ") || "-"}</p>
      </div>
    </Card>
  );
}
