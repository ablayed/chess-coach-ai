"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class AnalyzeRequest(BaseModel):
    fen: str
    depth: int = Field(default=20, ge=1, le=40)
    num_lines: int = Field(default=3, ge=1, le=5)


class Evaluation(BaseModel):
    type: Literal["cp", "mate"]
    value: int
    wdl: tuple[int, int, int] | None = None


class EngineLine(BaseModel):
    move: str
    san: str
    evaluation: Evaluation
    pv: list[str]
    pv_san: list[str]


class PositionConcepts(BaseModel):
    phase: str
    tactical_motifs: list[str]
    strategic_themes: list[str]
    king_safety: str


class AnalyzeResponse(BaseModel):
    fen: str
    evaluation: Evaluation
    best_moves: list[EngineLine]
    position_concepts: PositionConcepts


class CoachRequest(BaseModel):
    fen: str
    last_move: str | None = None
    user_move: str | None = None
    best_move: str
    evaluation_before: float
    evaluation_after: float
    concepts: PositionConcepts
    player_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"


class BookReference(BaseModel):
    source: str
    passage_summary: str
    relevance_score: float


class CoachResponse(BaseModel):
    explanation: str
    book_references: list[BookReference]
    key_concepts: list[str]
    move_classification: str
    cp_loss: float


class ReviewRequest(BaseModel):
    pgn: str | None = None
    lichess_url: str | None = None
    depth: int = Field(default=20, ge=8, le=30)
    player_color: Literal["white", "black"] = "white"

    @model_validator(mode="after")
    def validate_source(self) -> "ReviewRequest":
        if not self.pgn and not self.lichess_url:
            raise ValueError("Either pgn or lichess_url is required")
        return self


class ReviewMoveAnalysis(BaseModel):
    move_number: int
    move: str
    fen_before: str
    fen_after: str
    evaluation_before: float
    evaluation_after: float
    classification: str
    best_move: str
    is_critical: bool
    coaching: str | None = None


class ReviewSummary(BaseModel):
    accuracy: float
    move_classifications: dict[str, int]
    themes_to_improve: list[str]
    overall_coaching: str


class ReviewResponse(BaseModel):
    game_id: str
    status: str
    summary: ReviewSummary | None
    moves: list[ReviewMoveAnalysis]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    username: str = Field(min_length=3, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserPublic


class GameListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    white_player: str | None = None
    black_player: str | None = None
    result: str | None = None
    accuracy: float | None = None
    created_at: datetime


class GameDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pgn: str
    white_player: str | None = None
    black_player: str | None = None
    player_color: str | None = None
    result: str | None = None
    accuracy: float | None = None
    summary: dict | None = None
    moves: list[dict] | None = None
    source: str | None = None
    lichess_id: str | None = None
    created_at: datetime
