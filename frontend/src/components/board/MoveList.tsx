"use client";

import clsx from "clsx";
import { useEffect, useMemo, useRef } from "react";

import { MOVE_CLASS_COLORS } from "@/lib/constants";
import { useGameStore } from "@/stores/useGameStore";
import type { MoveClassMap } from "@/types/chess";

interface MoveListProps {
  classifications?: MoveClassMap;
}

export function MoveList({ classifications }: MoveListProps) {
  const moveHistory = useGameStore((state) => state.moveHistory);
  const currentMoveIndex = useGameStore((state) => state.currentMoveIndex);
  const goToMove = useGameStore((state) => state.goToMove);
  const goBack = useGameStore((state) => state.goBack);
  const goForward = useGameStore((state) => state.goForward);
  const containerRef = useRef<HTMLDivElement>(null);

  const rows = useMemo(() => {
    const grouped: Array<{ number: number; whiteIndex: number; blackIndex: number | null }> = [];
    for (let i = 0; i < moveHistory.length; i += 2) {
      grouped.push({ number: i / 2 + 1, whiteIndex: i, blackIndex: i + 1 < moveHistory.length ? i + 1 : null });
    }
    return grouped;
  }, [moveHistory]);

  useEffect(() => {
    const target = containerRef.current?.querySelector("[data-current='true']");
    if (target instanceof HTMLElement) {
      target.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [currentMoveIndex]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "ArrowLeft") {
        goBack();
      }
      if (event.key === "ArrowRight") {
        goForward();
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goBack, goForward]);

  return (
    <div ref={containerRef} className="max-h-72 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900/60 p-2">
      {rows.map((row) => {
        const whiteMove = moveHistory[row.whiteIndex];
        const blackMove = row.blackIndex !== null ? moveHistory[row.blackIndex] : null;
        const whiteClass = classifications?.[row.whiteIndex + 1];
        const blackClass = row.blackIndex !== null ? classifications?.[row.blackIndex + 1] : undefined;

        return (
          <div key={row.number} className="grid grid-cols-[auto_1fr_1fr] items-center gap-2 py-1 text-sm">
            <span className="text-gray-500">{row.number}.</span>
            <button
              data-current={currentMoveIndex === row.whiteIndex}
              onClick={() => goToMove(row.whiteIndex)}
              className={clsx(
                "flex items-center gap-1 rounded px-2 py-1 text-left transition",
                currentMoveIndex === row.whiteIndex ? "bg-cyan-500/20 text-cyan-200" : "text-gray-200 hover:bg-gray-700",
              )}
              type="button"
            >
              {whiteClass ? (
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: MOVE_CLASS_COLORS[whiteClass] ?? "#22c55e" }}
                />
              ) : null}
              {whiteMove?.san}
            </button>
            <button
              data-current={currentMoveIndex === row.blackIndex}
              onClick={() => {
                if (row.blackIndex !== null) {
                  goToMove(row.blackIndex);
                }
              }}
              className={clsx(
                "flex items-center gap-1 rounded px-2 py-1 text-left transition",
                currentMoveIndex === row.blackIndex ? "bg-cyan-500/20 text-cyan-200" : "text-gray-200 hover:bg-gray-700",
                row.blackIndex === null && "cursor-default opacity-40 hover:bg-transparent",
              )}
              type="button"
              disabled={row.blackIndex === null}
            >
              {blackClass ? (
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: MOVE_CLASS_COLORS[blackClass] ?? "#22c55e" }}
                />
              ) : null}
              {blackMove?.san ?? ""}
            </button>
          </div>
        );
      })}
    </div>
  );
}
