import type { PieceSymbol, Square } from "chess.js";

export type BoardOrientation = "white" | "black";

export interface MoveHistoryItem {
  from: Square;
  to: Square;
  san: string;
  lan: string;
  fen: string;
  color: "w" | "b";
  promotion?: PieceSymbol;
}

export interface CapturedPieces {
  white: string[];
  black: string[];
}

export interface MoveClassMap {
  [plyIndex: number]: string;
}
