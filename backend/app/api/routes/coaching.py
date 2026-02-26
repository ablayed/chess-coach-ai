import hashlib

import chess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.database import AnalysisCache
from app.models.schemas import CoachRequest, CoachResponse
from app.services.coaching_service import CoachingService
from app.core.concept_extractor import classify_move

router = APIRouter()


def coaching_cache_key(fen: str, user_move: str | None, player_level: str) -> str:
    """Generate a cache key specific to board position, move choice, and player level."""
    parts = fen.split()
    core = " ".join(parts[:4]) if len(parts) >= 4 else fen
    key_input = f"{core}|{user_move or 'none'}|{player_level}"
    return hashlib.sha256(key_input.encode("utf-8")).hexdigest()


@router.post("/coach/explain", response_model=CoachResponse)
async def coach_explain(
    request: CoachRequest,
    db: AsyncSession = Depends(get_db),
) -> CoachResponse:
    try:
        board = chess.Board(request.fen)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid FEN") from exc

    fen = board.fen()
    fen_hash = coaching_cache_key(fen, request.user_move, request.player_level)

    cp_loss = max(0.0, request.evaluation_before - request.evaluation_after) if request.user_move else 0.0
    classification = classify_move(cp_loss)

    cached: AnalysisCache | None = None
    cache_available = True

    try:
        cached = await db.get(AnalysisCache, fen_hash)
    except SQLAlchemyError:
        cache_available = False
        await db.rollback()

    if cached and cached.coaching_explanation:
        if cache_available:
            try:
                cached.hit_count += 1
                await db.commit()
            except SQLAlchemyError:
                await db.rollback()
        return CoachResponse.model_validate(
            {
                "explanation": cached.coaching_explanation,
                "book_references": cached.book_references or [],
                "key_concepts": request.concepts.strategic_themes + request.concepts.tactical_motifs,
                "move_classification": classification,
                "cp_loss": cp_loss,
            }
        )

    result = await CoachingService.explain_position(
        db=db,
        fen=fen,
        best_move=request.best_move,
        pv_lines=[{"san": request.best_move, "evaluation": {"type": "cp", "value": int(request.evaluation_after)}, "pv_san": []}],
        user_move=request.user_move,
        last_move=request.last_move,
        eval_before=request.evaluation_before,
        eval_after=request.evaluation_after,
        player_level=request.player_level,
    )

    if cache_available:
        try:
            if cached:
                cached.coaching_explanation = result["explanation"]
                cached.book_references = result["book_references"]
                cached.fen = fen
            else:
                cached = AnalysisCache(
                    fen_hash=fen_hash,
                    fen=fen,
                    coaching_explanation=result["explanation"],
                    book_references=result["book_references"],
                    hit_count=0,
                )
                db.add(cached)
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()

    return CoachResponse.model_validate(result)
