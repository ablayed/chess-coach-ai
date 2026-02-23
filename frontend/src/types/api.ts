export type EvalType = "cp" | "mate";

export interface Evaluation {
  type: EvalType;
  value: number;
  wdl?: [number, number, number] | null;
}

export interface EngineLine {
  move: string;
  san: string;
  evaluation: Evaluation;
  pv: string[];
  pv_san: string[];
  depth?: number;
}

export interface PositionConcepts {
  phase: string;
  tactical_motifs: string[];
  strategic_themes: string[];
  king_safety: string;
}

export interface AnalyzeResponse {
  fen: string;
  evaluation: Evaluation;
  best_moves: EngineLine[];
  position_concepts: PositionConcepts;
}

export interface AnalyzeRequest {
  fen: string;
  depth?: number;
  num_lines?: number;
}

export interface BookReference {
  source: string;
  passage_summary: string;
  relevance_score: number;
}

export interface CoachRequest {
  fen: string;
  last_move?: string;
  user_move?: string;
  best_move: string;
  evaluation_before: number;
  evaluation_after: number;
  concepts: PositionConcepts;
  player_level?: "beginner" | "intermediate" | "advanced";
}

export interface CoachResponse {
  explanation: string;
  book_references: BookReference[];
  key_concepts: string[];
  move_classification: string;
  cp_loss: number;
}

export interface ReviewRequest {
  pgn?: string;
  lichess_url?: string;
  depth?: number;
  player_color?: "white" | "black";
}

export interface ReviewMoveAnalysis {
  move_number: number;
  move: string;
  fen_before: string;
  fen_after: string;
  evaluation_before: number;
  evaluation_after: number;
  classification: string;
  best_move: string;
  is_critical: boolean;
  coaching?: string | null;
}

export interface ReviewSummary {
  accuracy: number;
  move_classifications: Record<string, number>;
  themes_to_improve: string[];
  overall_coaching: string;
}

export interface ReviewResponse {
  game_id: string;
  status: string;
  summary: ReviewSummary | null;
  moves: ReviewMoveAnalysis[];
}

export interface UserPublic {
  id: string;
  username: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserPublic;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface GameListItem {
  id: string;
  white_player?: string | null;
  black_player?: string | null;
  result?: string | null;
  accuracy?: number | null;
  created_at: string;
}

export interface GameDetail extends GameListItem {
  pgn: string;
  player_color?: string | null;
  summary?: Record<string, unknown> | null;
  moves?: Record<string, unknown>[] | null;
  source?: string | null;
  lichess_id?: string | null;
}

export interface ApiErrorResponse {
  detail?: string;
  message?: string;
}
