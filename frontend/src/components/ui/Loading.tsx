interface LoadingProps {
  label?: string;
}

export function Loading({ label = "Loading..." }: LoadingProps) {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-300">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-gray-500 border-t-cyan-400" />
      <span>{label}</span>
    </div>
  );
}
