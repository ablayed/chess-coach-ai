"use client";

import { ChangeEvent, useRef } from "react";

import { Button } from "@/components/ui/Button";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { useGameStore } from "@/stores/useGameStore";

interface BoardControlsProps {
  onImportPGN?: (pgn: string) => void;
}

export function BoardControls({ onImportPGN }: BoardControlsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const flipBoard = useGameStore((state) => state.flipBoard);
  const reset = useGameStore((state) => state.reset);
  const undo = useGameStore((state) => state.undo);
  const showArrows = useAnalysisStore((state) => state.showEngineArrows);
  const toggleArrows = useAnalysisStore((state) => state.toggleEngineArrows);

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handlePGNFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const text = await file.text();
    onImportPGN?.(text);
  };

  return (
    <div className="flex flex-wrap gap-2">
      <Button variant="secondary" size="sm" onClick={flipBoard}>
        Flip
      </Button>
      <Button variant="secondary" size="sm" onClick={undo}>
        Undo
      </Button>
      <Button variant="secondary" size="sm" onClick={reset}>
        Reset
      </Button>
      <button
        type="button"
        onClick={toggleArrows}
        className={`h-8 rounded-md px-3 text-sm font-medium transition-colors ${
          showArrows
            ? "border border-yellow-500/50 bg-yellow-500/20 text-yellow-300"
            : "border border-transparent bg-gray-700 text-gray-200 hover:bg-gray-600"
        }`}
        title={showArrows ? "Hide engine suggestion" : "Show engine suggestion"}
      >
        {showArrows ? "Hide Hint" : "Show Hint"}
      </button>
      <Button variant="ghost" size="sm" onClick={handleImportClick}>
        Import PGN
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pgn,.txt"
        onChange={handlePGNFile}
        className="hidden"
      />
    </div>
  );
}
