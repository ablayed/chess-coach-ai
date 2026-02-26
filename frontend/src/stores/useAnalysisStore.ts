import { create } from "zustand";

import { api, ApiError } from "@/lib/api";
import { subscribeToAnalysis, type AnalysisStreamPayload, type SSECleanup } from "@/lib/sse";
import type { AnalyzeResponse, CoachRequest, CoachResponse, PositionConcepts } from "@/types/api";

interface AnalysisState {
  isAnalyzing: boolean;
  currentAnalysis: AnalyzeResponse | null;
  coaching: CoachResponse | null;
  isLoadingCoaching: boolean;
  streamingDepth: number;
  showEngineArrows: boolean;
  error: string | null;
  sseCleanup: SSECleanup | null;
  analyzePosition: (fen: string, depth?: number, numLines?: number) => Promise<void>;
  getCoaching: (payload: CoachRequest) => Promise<void>;
  toggleEngineArrows: () => void;
  clearAnalysis: () => void;
}

const emptyConcepts: PositionConcepts = {
  phase: "unknown",
  tactical_motifs: [],
  strategic_themes: [],
  king_safety: "safe",
};

function streamPayloadToAnalysis(fen: string, payload: AnalysisStreamPayload): AnalyzeResponse {
  return {
    fen,
    evaluation: {
      type: payload.evaluation.type,
      value: payload.evaluation.value,
      wdl: null,
    },
    best_moves: [
      {
        move: payload.best_move,
        san: payload.best_move_san,
        evaluation: {
          type: payload.evaluation.type,
          value: payload.evaluation.value,
          wdl: null,
        },
        pv: payload.pv,
        pv_san: payload.pv,
      },
    ],
    position_concepts: emptyConcepts,
  };
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  isAnalyzing: false,
  currentAnalysis: null,
  coaching: null,
  isLoadingCoaching: false,
  streamingDepth: 0,
  showEngineArrows: false,
  error: null,
  sseCleanup: null,

  analyzePosition: async (fen, depth = 20, numLines = 3) => {
    const prevCleanup = get().sseCleanup;
    if (prevCleanup) {
      prevCleanup();
    }

    set({
      isAnalyzing: true,
      streamingDepth: 0,
      error: null,
      coaching: null,
      sseCleanup: null,
    });

    const cleanup = subscribeToAnalysis(
      fen,
      depth,
      (payload) => {
        set((state) => ({
          streamingDepth: payload.depth,
          currentAnalysis: state.currentAnalysis
            ? {
                ...state.currentAnalysis,
                evaluation: {
                  type: payload.evaluation.type,
                  value: payload.evaluation.value,
                  wdl: null,
                },
                best_moves: [
                  {
                    move: payload.best_move,
                    san: payload.best_move_san,
                    evaluation: {
                      type: payload.evaluation.type,
                      value: payload.evaluation.value,
                      wdl: null,
                    },
                    pv: payload.pv,
                    pv_san: payload.pv,
                  },
                ],
              }
            : streamPayloadToAnalysis(fen, payload),
        }));
      },
      () => {
        set({ isAnalyzing: false });
        void api
          .post<AnalyzeResponse>("/api/v1/analyze", { fen, depth, num_lines: numLines })
          .then((full) => set({ currentAnalysis: full, error: null, streamingDepth: depth }))
          .catch((err: unknown) => {
            const message = err instanceof ApiError ? err.detail : "Failed to fetch final analysis";
            set({ error: message });
          });
      },
      (error) => {
        set({ isAnalyzing: false, error: error.message });
        void api
          .post<AnalyzeResponse>("/api/v1/analyze", { fen, depth, num_lines: numLines })
          .then((full) => set({ currentAnalysis: full, error: null, streamingDepth: depth }))
          .catch((err: unknown) => {
            const message = err instanceof ApiError ? err.detail : "Analysis failed";
            set({ error: message });
          });
      },
    );

    set({ sseCleanup: cleanup });
  },

  getCoaching: async (payload) => {
    set({ isLoadingCoaching: true, error: null });
    try {
      const response = await api.post<CoachResponse>("/api/v1/coach/explain", payload);
      set({ coaching: response, isLoadingCoaching: false });
    } catch (error: unknown) {
      const message = error instanceof ApiError ? error.detail : "Coaching request failed";
      set({ isLoadingCoaching: false, error: message });
    }
  },

  toggleEngineArrows: () => {
    set((state) => ({ showEngineArrows: !state.showEngineArrows }));
  },

  clearAnalysis: () => {
    const cleanup = get().sseCleanup;
    if (cleanup) {
      cleanup();
    }
    set({
      isAnalyzing: false,
      currentAnalysis: null,
      coaching: null,
      isLoadingCoaching: false,
      streamingDepth: 0,
      error: null,
      sseCleanup: null,
    });
  },
}));
