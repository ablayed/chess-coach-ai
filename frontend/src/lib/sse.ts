import { API_BASE_URL } from "@/lib/api";

export interface AnalysisStreamPayload {
  depth: number;
  evaluation: {
    type: "cp" | "mate";
    value: number;
  };
  best_move: string;
  best_move_san: string;
  pv: string[];
  nodes: number;
}

export type SSECleanup = () => void;

export function subscribeToAnalysis(
  fen: string,
  depth: number,
  onData: (data: AnalysisStreamPayload) => void,
  onDone: () => void,
  onError: (error: Error) => void,
): SSECleanup {
  const url = `${API_BASE_URL}/api/v1/analyze/stream?fen=${encodeURIComponent(fen)}&depth=${depth}`;
  const eventSource = new EventSource(url);

  eventSource.addEventListener("analysis", (event: MessageEvent) => {
    try {
      const payload = JSON.parse(event.data) as AnalysisStreamPayload;
      onData(payload);
    } catch {
      onError(new Error("Failed to parse analysis stream payload"));
    }
  });

  eventSource.addEventListener("done", () => {
    onDone();
    eventSource.close();
  });

  eventSource.onerror = () => {
    onError(new Error("SSE connection error"));
    eventSource.close();
  };

  return () => eventSource.close();
}
