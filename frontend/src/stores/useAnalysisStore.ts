import { create } from "zustand";

import { api, ApiError } from "@/lib/api";
import { connectAnalysisStream, type AnalysisStreamPayload, type SSEClient } from "@/lib/sse";
import type { AnalyzeResponse, CoachRequest, CoachResponse, PositionConcepts } from "@/types/api";

interface AnalysisState {
  isAnalyzing: boolean;
  currentAnalysis: AnalyzeResponse | null;
  coaching: CoachResponse | null;
  isLoadingCoaching: boolean;
  streamingDepth: number;
  error: string | null;
  streamClient: SSEClient | null;
  analyzePosition: (fen: string, depth?: number, numLines?: number) => Promise<void>;
  getCoaching: (payload: CoachRequest) => Promise<void>;
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
  error: null,
  streamClient: null,

  analyzePosition: async (fen, depth = 20, numLines = 3) => {
    const current = get().streamClient;
    current?.close();

    set({
      isAnalyzing: true,
      streamingDepth: 0,
      error: null,
      coaching: null,
      streamClient: null,
    });

    const streamClient = connectAnalysisStream({
      fen,
      depth,
      onMessage: (payload) => {
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
      onError: (message) => {
        set({ error: message });
      },
    });

    set({ streamClient });

    try {
      const response = await api.post<AnalyzeResponse>("/api/v1/analyze", {
        fen,
        depth,
        num_lines: numLines,
      });

      set({
        currentAnalysis: response,
        isAnalyzing: false,
        streamingDepth: depth,
        error: null,
      });
    } catch (error: unknown) {
      const message = error instanceof ApiError ? error.detail : "Analysis failed";
      set({
        isAnalyzing: false,
        error: message,
      });
    } finally {
      streamClient.close();
      set({ streamClient: null });
    }
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

  clearAnalysis: () => {
    const streamClient = get().streamClient;
    streamClient?.close();
    set({
      isAnalyzing: false,
      currentAnalysis: null,
      coaching: null,
      isLoadingCoaching: false,
      streamingDepth: 0,
      error: null,
      streamClient: null,
    });
  },
}));
