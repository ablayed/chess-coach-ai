import { Chess, Move, PieceSymbol, Square } from "chess.js";
import { create } from "zustand";

import type { BoardOrientation, MoveHistoryItem } from "@/types/chess";

interface GameState {
  chess: Chess;
  initialFen: string;
  fen: string;
  moveHistory: MoveHistoryItem[];
  currentMoveIndex: number;
  orientation: BoardOrientation;
  makeMove: (from: Square, to: Square, promotion?: PieceSymbol) => boolean;
  undo: () => void;
  goToMove: (index: number) => void;
  goForward: () => void;
  goBack: () => void;
  reset: () => void;
  loadPGN: (pgn: string) => boolean;
  loadMovesFromSan: (moves: string[], initialFen?: string) => boolean;
  flipBoard: () => void;
  setFEN: (fen: string) => boolean;
}

const START_FEN = new Chess().fen();

function toHistoryItem(move: Move, fen: string): MoveHistoryItem {
  return {
    from: move.from,
    to: move.to,
    san: move.san,
    lan: move.lan,
    fen,
    color: move.color,
    promotion: move.promotion,
  };
}

function rebuildBoard(initialFen: string, moves: MoveHistoryItem[], upToIndex: number): Chess {
  const board = new Chess(initialFen);
  for (let i = 0; i <= upToIndex; i += 1) {
    const move = moves[i];
    if (!move) {
      break;
    }
    board.move({ from: move.from, to: move.to, promotion: move.promotion });
  }
  return board;
}

function buildHistoryFromVerbose(initialFen: string, verboseMoves: Move[]): MoveHistoryItem[] {
  const board = new Chess(initialFen);
  const history: MoveHistoryItem[] = [];
  verboseMoves.forEach((mv) => {
    const move = board.move({ from: mv.from, to: mv.to, promotion: mv.promotion }) as Move | null;
    if (move) {
      history.push(toHistoryItem(move, board.fen()));
    }
  });
  return history;
}

export const useGameStore = create<GameState>((set, get) => ({
  chess: new Chess(),
  initialFen: START_FEN,
  fen: START_FEN,
  moveHistory: [],
  currentMoveIndex: -1,
  orientation: "white",

  makeMove: (from, to, promotion) => {
    const { chess, moveHistory, currentMoveIndex, initialFen } = get();

    let workingBoard = chess;
    let workingHistory = moveHistory;
    if (currentMoveIndex < moveHistory.length - 1) {
      workingHistory = moveHistory.slice(0, currentMoveIndex + 1);
      workingBoard = rebuildBoard(initialFen, workingHistory, workingHistory.length - 1);
    }

    const move = workingBoard.move({ from, to, promotion });
    if (!move) {
      return false;
    }

    const nextHistory = [...workingHistory, toHistoryItem(move, workingBoard.fen())];
    set({
      chess: workingBoard,
      fen: workingBoard.fen(),
      moveHistory: nextHistory,
      currentMoveIndex: nextHistory.length - 1,
    });
    return true;
  },

  undo: () => {
    const { currentMoveIndex } = get();
    if (currentMoveIndex < 0) {
      return;
    }
    get().goToMove(currentMoveIndex - 1);
  },

  goToMove: (index) => {
    const { moveHistory, initialFen } = get();
    const clamped = Math.max(-1, Math.min(index, moveHistory.length - 1));
    const board = rebuildBoard(initialFen, moveHistory, clamped);
    set({
      chess: board,
      fen: board.fen(),
      currentMoveIndex: clamped,
    });
  },

  goForward: () => {
    const { currentMoveIndex, moveHistory } = get();
    if (currentMoveIndex >= moveHistory.length - 1) {
      return;
    }
    get().goToMove(currentMoveIndex + 1);
  },

  goBack: () => {
    const { currentMoveIndex } = get();
    if (currentMoveIndex <= -1) {
      return;
    }
    get().goToMove(currentMoveIndex - 1);
  },

  reset: () => {
    const board = new Chess();
    set({
      chess: board,
      initialFen: board.fen(),
      fen: board.fen(),
      moveHistory: [],
      currentMoveIndex: -1,
    });
  },

  loadPGN: (pgn) => {
    const parsedBoard = new Chess();
    try {
      parsedBoard.loadPgn(pgn);
    } catch {
      return false;
    }

    const verbose = parsedBoard.history({ verbose: true });
    const start = new Chess();
    const history = buildHistoryFromVerbose(start.fen(), verbose);
    const finalBoard = rebuildBoard(start.fen(), history, history.length - 1);

    set({
      chess: finalBoard,
      initialFen: start.fen(),
      fen: finalBoard.fen(),
      moveHistory: history,
      currentMoveIndex: history.length - 1,
    });
    return true;
  },

  loadMovesFromSan: (moves, initialFen = START_FEN) => {
    let board: Chess;
    try {
      board = new Chess(initialFen);
    } catch {
      return false;
    }

    const history: MoveHistoryItem[] = [];
    for (const san of moves) {
      const move = board.move(san);
      if (!move) {
        return false;
      }
      history.push(toHistoryItem(move, board.fen()));
    }

    set({
      chess: board,
      initialFen,
      fen: board.fen(),
      moveHistory: history,
      currentMoveIndex: history.length - 1,
    });
    return true;
  },

  flipBoard: () => {
    set((state) => ({ orientation: state.orientation === "white" ? "black" : "white" }));
  },

  setFEN: (fen) => {
    try {
      const board = new Chess(fen);
      set({
        chess: board,
        initialFen: board.fen(),
        fen: board.fen(),
        moveHistory: [],
        currentMoveIndex: -1,
      });
      return true;
    } catch {
      return false;
    }
  },
}));
