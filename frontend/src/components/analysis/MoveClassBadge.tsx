interface MoveClassBadgeProps {
  classification: string;
}

const CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  brilliant: { label: "!! BRILLIANT", bg: "bg-cyan-500/20", text: "text-cyan-400" },
  great: { label: "! GREAT", bg: "bg-green-500/20", text: "text-green-400" },
  good: { label: "GOOD", bg: "bg-green-400/20", text: "text-green-300" },
  inaccuracy: { label: "?! INACCURACY", bg: "bg-yellow-500/20", text: "text-yellow-400" },
  mistake: { label: "? MISTAKE", bg: "bg-orange-500/20", text: "text-orange-400" },
  blunder: { label: "?? BLUNDER", bg: "bg-red-500/20", text: "text-red-400" },
};

export function MoveClassBadge({ classification }: MoveClassBadgeProps) {
  const normalized = classification.toLowerCase();
  const current = CONFIG[normalized] ?? {
    label: normalized.toUpperCase(),
    bg: "bg-gray-500/20",
    text: "text-gray-400",
  };

  return (
    <span className={`rounded px-2 py-0.5 text-xs font-bold ${current.bg} ${current.text}`}>{current.label}</span>
  );
}
