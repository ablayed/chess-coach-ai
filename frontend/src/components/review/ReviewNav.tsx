"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { isTextInputFocused } from "@/lib/dom-utils";

interface ReviewNavProps {
  currentMove: number;
  totalMoves: number;
  onFirst: () => void;
  onBack: () => void;
  onForward: () => void;
  onLast: () => void;
}

export function ReviewNav({
  currentMove,
  totalMoves,
  onFirst,
  onBack,
  onForward,
  onLast,
}: ReviewNavProps) {
  const [autoplay, setAutoplay] = useState(false);

  useEffect(() => {
    if (!autoplay) {
      return;
    }
    const id = setInterval(() => {
      if (currentMove >= totalMoves - 1) {
        setAutoplay(false);
      } else {
        onForward();
      }
    }, 1500);

    return () => clearInterval(id);
  }, [autoplay, currentMove, totalMoves, onForward]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (isTextInputFocused()) {
        return;
      }

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        onBack();
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        onForward();
      }
      if (event.key === "Home") {
        event.preventDefault();
        onFirst();
      }
      if (event.key === "End") {
        event.preventDefault();
        onLast();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onBack, onFirst, onForward, onLast]);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="secondary" size="sm" onClick={onFirst}>
        First
      </Button>
      <Button variant="secondary" size="sm" onClick={onBack}>
        Back
      </Button>
      <Button variant="secondary" size="sm" onClick={onForward}>
        Forward
      </Button>
      <Button variant="secondary" size="sm" onClick={onLast}>
        Last
      </Button>
      <Button variant={autoplay ? "primary" : "ghost"} size="sm" onClick={() => setAutoplay((prev) => !prev)}>
        {autoplay ? "Stop" : "Auto-play"}
      </Button>
      <span className="ml-auto text-sm text-gray-300">
        Move {Math.max(currentMove + 1, 0)}/{totalMoves}
      </span>
    </div>
  );
}
