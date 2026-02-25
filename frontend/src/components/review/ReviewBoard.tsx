"use client";

import dynamic from "next/dynamic";
import clsx from "clsx";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MoveClassBadge } from "@/components/analysis/MoveClassBadge";
import { useBoardWidth } from "@/hooks/useBoardWidth";
import { isTextInputFocused } from "@/lib/dom-utils";
import type { ReviewMoveAnalysis } from "@/types/api";

const Chessboard = dynamic(
  () => import("react-chessboard").then((mod) => mod.Chessboard),
  { ssr: false },
);

interface ReviewBoardProps {
  moves: ReviewMoveAnalysis[];
  playerColor: "white" | "black";
}

const classColors: Record<string, string> = {
  brilliant: "text-cyan-400",
  great: "text-green-400",
  good: "text-green-300",
  inaccuracy: "text-yellow-400",
  mistake: "text-orange-400",
  blunder: "text-red-400",
};

export function ReviewBoard({ moves, playerColor }: ReviewBoardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const boardWidth = useBoardWidth(420);
  const currentMove = moves[currentIndex];

  useEffect(() => {
    setCurrentIndex(0);
  }, [moves]);

  const goTo = useCallback(
    (idx: number) => setCurrentIndex(Math.max(0, Math.min(moves.length - 1, idx))),
    [moves.length],
  );
  const goBack = useCallback(() => goTo(currentIndex - 1), [goTo, currentIndex]);
  const goForward = useCallback(() => goTo(currentIndex + 1), [goTo, currentIndex]);
  const goFirst = useCallback(() => goTo(0), [goTo]);
  const goLast = useCallback(() => goTo(moves.length - 1), [goTo, moves.length]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (isTextInputFocused()) {
        return;
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goBack();
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        goForward();
      }
      if (event.key === "Home") {
        event.preventDefault();
        goFirst();
      }
      if (event.key === "End") {
        event.preventDefault();
        goLast();
      }
    },
    [goBack, goFirst, goForward, goLast],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const moveRows = useMemo(
    () =>
      moves.map((move, idx) => {
        const moveNumber = Math.ceil(move.move_number / 2);
        const suffix = move.move_number % 2 === 1 ? "." : "...";
        return { idx, move, label: `${moveNumber}${suffix} ${move.move}` };
      }),
    [moves],
  );

  if (!moves.length || !currentMove) {
    return null;
  }

  return (
    <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="lg:col-span-1">
        <div className="overflow-x-auto">
          <Chessboard
            position={currentMove.fen_after}
            boardWidth={boardWidth}
            isDraggablePiece={() => false}
            boardOrientation={playerColor === "black" ? "black" : "white"}
            customDarkSquareStyle={{ backgroundColor: "#779952" }}
            customLightSquareStyle={{ backgroundColor: "#edeed1" }}
          />
        </div>

        <div className="mt-4 flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={goFirst}
            className="rounded bg-gray-800 px-3 py-2 text-gray-300 transition hover:bg-gray-700"
          >
            |&lt;
          </button>
          <button
            type="button"
            onClick={goBack}
            className="rounded bg-gray-800 px-4 py-2 text-gray-300 transition hover:bg-gray-700"
          >
            &lt;
          </button>
          <span className="px-2 text-sm text-gray-400">
            Move {currentIndex + 1} / {moves.length}
          </span>
          <button
            type="button"
            onClick={goForward}
            className="rounded bg-gray-800 px-4 py-2 text-gray-300 transition hover:bg-gray-700"
          >
            &gt;
          </button>
          <button
            type="button"
            onClick={goLast}
            className="rounded bg-gray-800 px-3 py-2 text-gray-300 transition hover:bg-gray-700"
          >
            &gt;|
          </button>
        </div>
      </div>

      <div className="max-h-[500px] overflow-y-auto rounded-lg border border-gray-700 bg-gray-800 p-4 lg:col-span-1">
        <h3 className="mb-3 text-sm font-bold text-gray-400">Moves</h3>
        <div className="space-y-1">
          {moveRows.map(({ idx, move, label }) => (
            <button
              key={`${move.move_number}-${move.move}`}
              type="button"
              onClick={() => goTo(idx)}
              className={clsx(
                "flex w-full items-center justify-between rounded px-3 py-1.5 text-left text-sm transition",
                idx === currentIndex ? "border border-cyan-600 bg-cyan-900/40" : "hover:bg-gray-700",
              )}
            >
              <span className={classColors[move.classification] ?? "text-gray-300"}>{label}</span>
              <span className="text-xs text-gray-500">
                {move.evaluation_after >= 0 ? "+" : ""}
                {(move.evaluation_after / 100).toFixed(1)}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4 lg:col-span-1">
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-4">
          <div className="mb-2 flex items-center gap-3">
            <span className="text-lg font-bold text-gray-100">{currentMove.move}</span>
            <MoveClassBadge classification={currentMove.classification} />
          </div>
          {!["great", "good", "brilliant"].includes(currentMove.classification) ? (
            <p className="text-sm text-gray-400">
              Best was: <span className="font-mono text-green-400">{currentMove.best_move}</span>
            </p>
          ) : null}
          <p className="mt-1 text-sm text-gray-500">
            Eval: {(currentMove.evaluation_before / 100).toFixed(1)} {"->"} {(currentMove.evaluation_after / 100).toFixed(1)}
          </p>
        </div>

        {currentMove.coaching ? (
          <div className="rounded-lg border border-gray-700 bg-gray-800 p-4">
            <h3 className="mb-2 text-sm font-bold text-cyan-400">Coach says:</h3>
            <p className="text-sm leading-relaxed text-gray-300">{currentMove.coaching}</p>
          </div>
        ) : null}

        {!currentMove.coaching && currentMove.is_critical ? (
          <div className="rounded-lg border border-gray-700 bg-gray-800 p-4 text-sm text-gray-500">
            Coaching explanation not available for this move.
          </div>
        ) : null}
      </div>
    </div>
  );
}
