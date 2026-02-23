import { Chess, PieceSymbol, SQUARES, Square } from "chess.js";

import type { Evaluation } from "@/types/api";

export function validateFen(fen: string): boolean {
  try {
    const board = new Chess(fen);
    return Boolean(board.fen());
  } catch {
    return false;
  }
}

export function parseLichessGameId(input: string): string | null {
  const pattern = /(?:https?:\/\/)?(?:www\.)?lichess\.org\/(?:game\/)?([a-zA-Z0-9]{8})(?:\/\w+)?/;
  const match = input.trim().match(pattern);
  return match ? match[1] : null;
}

export function normalizeEvalToWhiteCp(evaluation: Evaluation): number {
  if (evaluation.type === "mate") {
    const sign = evaluation.value >= 0 ? 1 : -1;
    return sign * (10000 - Math.min(Math.abs(evaluation.value), 99) * 100);
  }
  return evaluation.value;
}

export function formatEvaluation(evaluation: Evaluation | null | undefined): string {
  if (!evaluation) {
    return "0.0";
  }
  if (evaluation.type === "mate") {
    return `M${evaluation.value}`;
  }
  return `${evaluation.value >= 0 ? "+" : ""}${(evaluation.value / 100).toFixed(1)}`;
}

export function sigmoidFromCp(cp: number): number {
  return 1 / (1 + Math.exp(-cp / 400));
}

export function guessPromotion(from: Square, to: Square, piece: string): PieceSymbol | undefined {
  if (piece.toLowerCase() !== "p") {
    return undefined;
  }
  if (from[1] === "7" && to[1] === "8") {
    return "q";
  }
  if (from[1] === "2" && to[1] === "1") {
    return "q";
  }
  return undefined;
}

const START_COUNTS: Record<string, number> = {
  p: 8,
  n: 2,
  b: 2,
  r: 2,
  q: 1,
};

const PIECE_SYMBOLS: Record<string, string> = {
  wp: "?",
  wn: "?",
  wb: "?",
  wr: "?",
  wq: "?",
  bp: "?",
  bn: "?",
  bb: "?",
  br: "?",
  bq: "?",
};

export function getCapturedPieces(board: Chess): { white: string[]; black: string[] } {
  const counts: Record<string, number> = {
    wp: 0,
    wn: 0,
    wb: 0,
    wr: 0,
    wq: 0,
    bp: 0,
    bn: 0,
    bb: 0,
    br: 0,
    bq: 0,
  };

  for (const square of SQUARES) {
    const piece = board.get(square);
    if (!piece || piece.type === "k") {
      continue;
    }
    const key = `${piece.color}${piece.type}` as keyof typeof counts;
    counts[key] += 1;
  }

  const missingWhite: string[] = [];
  const missingBlack: string[] = [];

  (Object.keys(START_COUNTS) as Array<keyof typeof START_COUNTS>).forEach((type) => {
    const whiteMissing = START_COUNTS[type] - counts[`w${type}`];
    const blackMissing = START_COUNTS[type] - counts[`b${type}`];

    for (let i = 0; i < whiteMissing; i += 1) {
      missingWhite.push(PIECE_SYMBOLS[`w${type}`]);
    }
    for (let i = 0; i < blackMissing; i += 1) {
      missingBlack.push(PIECE_SYMBOLS[`b${type}`]);
    }
  });

  return { white: missingWhite, black: missingBlack };
}
