import clsx from "clsx";

import { MOVE_CLASS_BADGE } from "@/lib/constants";

interface MoveClassBadgeProps {
  classification: string;
}

const ICON_MAP: Record<string, string> = {
  brilliant: "!!",
  great: "!",
  good: "=",
  inaccuracy: "?!",
  mistake: "?",
  blunder: "??",
};

export function MoveClassBadge({ classification }: MoveClassBadgeProps) {
  const normalized = classification.toLowerCase();
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-md border px-2 py-1 text-xs font-semibold uppercase tracking-wide",
        MOVE_CLASS_BADGE[normalized] ?? "border-gray-600 bg-gray-700 text-gray-200",
      )}
    >
      <span className="mr-1">{ICON_MAP[normalized] ?? "-"}</span>
      {normalized}
    </span>
  );
}
