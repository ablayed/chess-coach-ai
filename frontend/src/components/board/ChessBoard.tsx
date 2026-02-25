"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { PieceSymbol, SQUARES, Square } from "chess.js";

import { useBoardWidth } from "@/hooks/useBoardWidth";
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
  const responsiveWidth = useBoardWidth(620);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(620);

  const chess = useGameStore((state) => state.chess);
  const fen = useGameStore((state) => state.fen);
  const orientation = useGameStore((state) => state.orientation);
  const moveHistory = useGameStore((state) => state.moveHistory);
  const currentMoveIndex = useGameStore((state) => state.currentMoveIndex);
  const makeMove = useGameStore((state) => state.makeMove);

  const analyzePosition = useAnalysisStore((state) => state.analyzePosition);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }

    const observer = new ResizeObserver((entries) => {
      const nextWidth = Math.floor(entries[0]?.contentRect.width ?? 0);
      if (nextWidth > 0) {
        setContainerWidth(nextWidth);
      }
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const boardWidth = useMemo(
    () => Math.max(240, Math.min(responsiveWidth, containerWidth)),
    [containerWidth, responsiveWidth],
  );

  const bestMove = bestMoveOverride ?? currentAnalysis?.best_moves[0]?.move ?? null;
  const turn = chess.turn();

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

  const isPromotionMove = (sourceSquare: string, targetSquare: string, piece: string): boolean => {
    const normalizedPiece = piece.toLowerCase();
    if (normalizedPiece !== "wp" && normalizedPiece !== "bp") {
      return false;
    }
    if (sourceSquare.length < 2 || targetSquare.length < 2) {
      return false;
    }
    if (sourceSquare[1] === "7" && targetSquare[1] === "8") {
      return true;
    }
    if (sourceSquare[1] === "2" && targetSquare[1] === "1") {
      return true;
    }
    return false;
  };

  const tryMove = (
    sourceSquare: string,
    targetSquare: string,
    piece: string,
    forcedPromotion?: PieceSymbol,
  ): boolean => {
    try {
      const from = sourceSquare as Square;
      const to = targetSquare as Square;
      const promotion = forcedPromotion ?? (guessPromotion(from, to, piece) as PieceSymbol | undefined);
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
    } catch (error) {
      // Keep board stable on invalid drags; react-chessboard will snap piece back.
      console.warn("Invalid move:", error);
      return false;
    }
  };

  const onPieceDrop = (sourceSquare: string, targetSquare: string, piece: string) => {
    if (!interactive) {
      return false;
    }

    if (isPromotionMove(sourceSquare, targetSquare, piece)) {
      return true;
    }

    return tryMove(sourceSquare, targetSquare, piece);
  };

  return (
    <div ref={containerRef} className="w-full overflow-x-auto">
      <Chessboard
        id="chesscoach-board"
        position={fen}
        onPieceDrop={onPieceDrop}
        onPromotionCheck={isPromotionMove}
        onPromotionPieceSelect={(piece, promoteFromSquare, promoteToSquare) => {
          if (!interactive) {
            return false;
          }
          const selectedPiece = piece ?? "";
          const promotion = selectedPiece.charAt(1).toLowerCase() as PieceSymbol | undefined;
          if (!promotion || !promoteFromSquare || !promoteToSquare) {
            return false;
          }
          return tryMove(promoteFromSquare, promoteToSquare, selectedPiece, promotion);
        }}
        isDraggablePiece={({ piece }) => interactive && Boolean(piece) && piece.charAt(0).toLowerCase() === turn}
        boardOrientation={orientation}
        boardWidth={boardWidth}
        customArrows={bestArrow}
        customSquareStyles={customSquareStyles}
        showBoardNotation
      />
    </div>
  );
}
