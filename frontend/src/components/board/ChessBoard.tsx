"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { PieceSymbol, SQUARES, Square } from "chess.js";

import { guessPromotion } from "@/lib/chess-utils";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { useGameStore } from "@/stores/useGameStore";

const Chessboard = dynamic(
  () => import("react-chessboard").then((mod) => mod.Chessboard),
  { ssr: false },
);

interface ChessBoardProps {
  interactive?: boolean;
  bestMoveOverride?: string | null;
  onMovePlayed?: (san: string, fen: string) => void;
}

function findCheckedKingSquare(fen: string, sideToMove: "w" | "b"): Square | null {
  const boardPart = fen.split(" ")[0] ?? "";
  if (!boardPart) {
    return null;
  }
  const ranks = boardPart.split("/");
  const king = sideToMove === "w" ? "K" : "k";

  for (let rankIndex = 0; rankIndex < ranks.length; rankIndex += 1) {
    const rank = ranks[rankIndex] ?? "";
    let file = 0;
    for (const char of rank) {
      if (/\d/.test(char)) {
        file += Number(char);
      } else {
        if (char === king) {
          const square = `${"abcdefgh"[file]}${8 - rankIndex}` as Square;
          return square;
        }
        file += 1;
      }
    }
  }
  return null;
}

export function ChessBoard({ interactive = true, bestMoveOverride, onMovePlayed }: ChessBoardProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [boardWidth, setBoardWidth] = useState(320);

  const chess = useGameStore((state) => state.chess);
  const fen = useGameStore((state) => state.fen);
  const orientation = useGameStore((state) => state.orientation);
  const moveHistory = useGameStore((state) => state.moveHistory);
  const currentMoveIndex = useGameStore((state) => state.currentMoveIndex);
  const makeMove = useGameStore((state) => state.makeMove);

  const analyzePosition = useAnalysisStore((state) => state.analyzePosition);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 320;
      setBoardWidth(Math.min(600, Math.max(240, Math.floor(width))));
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const bestMove = bestMoveOverride ?? currentAnalysis?.best_moves[0]?.move ?? null;
  const bestArrow = useMemo<Array<[Square, Square]>>(() => {
    if (!bestMove || bestMove.length < 4) {
      return [] as Array<[Square, Square]>;
    }
    const from = bestMove.slice(0, 2) as Square;
    const to = bestMove.slice(2, 4) as Square;
    if (!SQUARES.includes(from) || !SQUARES.includes(to)) {
      return [] as Array<[Square, Square]>;
    }
    return [[from, to]];
  }, [bestMove]);

  const customSquareStyles = useMemo(() => {
    const styles: Record<string, Record<string, string | number>> = {};
    const last = moveHistory[currentMoveIndex];

    if (last) {
      styles[last.from] = { backgroundColor: "rgba(250, 204, 21, 0.35)" };
      styles[last.to] = { backgroundColor: "rgba(250, 204, 21, 0.35)" };
    }

    if (chess.inCheck()) {
      const checked = findCheckedKingSquare(fen, chess.turn());
      if (checked) {
        styles[checked] = { backgroundColor: "rgba(239, 68, 68, 0.45)" };
      }
    }

    return styles;
  }, [moveHistory, currentMoveIndex, chess, fen]);

  const onPieceDrop = (sourceSquare: string, targetSquare: string, piece: string) => {
    if (!interactive) {
      return false;
    }

    const from = sourceSquare as Square;
    const to = targetSquare as Square;
    const promotion = guessPromotion(from, to, piece) as PieceSymbol | undefined;

    const moved = makeMove(from, to, promotion);
    if (!moved) {
      return false;
    }

    const { fen: nextFen, moveHistory: nextHistory } = useGameStore.getState();
    const latestMove = nextHistory[nextHistory.length - 1];
    if (latestMove) {
      onMovePlayed?.(latestMove.san, nextFen);
    }
    analyzePosition(nextFen).catch(() => undefined);
    return true;
  };

  return (
    <div ref={containerRef} className="w-full">
      <Chessboard
        id="chesscoach-board"
        position={fen}
        onPieceDrop={onPieceDrop}
        boardOrientation={orientation}
        boardWidth={boardWidth}
        customArrows={bestArrow}
        customSquareStyles={customSquareStyles}
        showBoardNotation
      />
    </div>
  );
}
