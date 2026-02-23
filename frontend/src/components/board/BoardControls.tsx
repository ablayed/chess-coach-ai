"use client";

import { ChangeEvent, useRef } from "react";

import { Button } from "@/components/ui/Button";
import { useGameStore } from "@/stores/useGameStore";

interface BoardControlsProps {
  onImportPGN?: (pgn: string) => void;
}

export function BoardControls({ onImportPGN }: BoardControlsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const flipBoard = useGameStore((state) => state.flipBoard);
  const reset = useGameStore((state) => state.reset);
  const undo = useGameStore((state) => state.undo);

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
