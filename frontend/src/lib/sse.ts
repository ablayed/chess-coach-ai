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

interface ConnectAnalysisStreamOptions {
  fen: string;
  depth: number;
  onMessage: (payload: AnalysisStreamPayload) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
  reconnect?: boolean;
}

export interface SSEClient {
  close: () => void;
  readonly readyState: number;
}

export function connectAnalysisStream(options: ConnectAnalysisStreamOptions): SSEClient {
  const { fen, depth, onMessage, onDone, onError, reconnect = true } = options;
  let attempts = 0;
  let closed = false;
  let source: EventSource | null = null;

  const connect = (): void => {
    const url = `${API_BASE_URL}/api/v1/analyze/stream?fen=${encodeURIComponent(fen)}&depth=${depth}`;
    source = new EventSource(url);

    source.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as AnalysisStreamPayload;
        onMessage(parsed);
      } catch {
        onError?.("Invalid stream payload received.");
      }
    };

    source.addEventListener("done", () => {
      onDone?.();
    });

    source.onerror = () => {
      if (closed) {
        return;
      }
      onError?.("Analysis stream disconnected.");
      source?.close();
      if (reconnect && attempts < 2) {
        attempts += 1;
        setTimeout(connect, 800 * attempts);
      }
    };
  };

  connect();

  return {
    close: () => {
      closed = true;
      source?.close();
    },
    get readyState() {
      return source?.readyState ?? EventSource.CLOSED;
    },
  };
}
