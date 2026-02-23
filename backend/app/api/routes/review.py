import io
import re
import uuid
from collections import Counter

import chess
import chess.pgn
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user, get_stockfish_pool
from app.core.concept_extractor import classify_move, extract_concepts
from app.core.prompt_templates import GAME_SUMMARY_PROMPT
from app.core.stockfish_pool import StockfishPool
from app.db.session import get_db
from app.models.database import Game, User
from app.models.schemas import ReviewMoveAnalysis, ReviewRequest, ReviewResponse, ReviewSummary
from app.services.coaching_service import CoachingService, llm_service

router = APIRouter()


def _extract_lichess_game_id(url: str) -> str:
    pattern = re.compile(r"(?:https?://)?(?:www\.)?lichess\.org/(?:game/)?([a-zA-Z0-9]{8})(?:/\w+)?")
    match = pattern.search(url.strip())
    if not match:
        raise ValueError("Invalid Lichess URL")
    return match.group(1)


async def _fetch_lichess_pgn(game_id: str) -> str:
    export_url = f"https://lichess.org/game/export/{game_id}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(export_url, headers={"Accept": "application/x-chess-pgn"})
        response.raise_for_status()
        text = response.text.strip()
        if not text:
            raise ValueError("Empty PGN from Lichess")
        return text


def _evaluation_to_cp(eval_payload: dict) -> float:
    eval_type = eval_payload.get("type", "cp")
    value = float(eval_payload.get("value", 0))
    if eval_type == "mate":
        sign = 1 if value >= 0 else -1
        return float(sign * (10000 - min(abs(value), 9999) * 100))
    return value


def _move_accuracy(cp_loss: float) -> float:
    return max(0.0, 100.0 - min(100.0, cp_loss / 5.0))


@router.post("/review/game", response_model=ReviewResponse)
async def review_game(
    request: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    pool: StockfishPool = Depends(get_stockfish_pool),
    current_user: User | None = Depends(get_optional_user),
) -> ReviewResponse:
    pgn_text = request.pgn
    source = "pgn_import"
    lichess_id: str | None = None

    if request.lichess_url:
        try:
            lichess_id = _extract_lichess_game_id(request.lichess_url)
            pgn_text = await _fetch_lichess_pgn(lichess_id)
            source = "lichess"
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to import Lichess game: {exc}") from exc

    if not pgn_text:
        raise HTTPException(status_code=400, detail="PGN input is required")

    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise HTTPException(status_code=400, detail="Unable to parse PGN")

    board = game.board()
    move_analyses: list[ReviewMoveAnalysis] = []

    player_classifications: Counter[str] = Counter()
    theme_counter: Counter[str] = Counter()
    critical_moves: list[int] = []
    player_move_scores: list[float] = []

    for ply_index, move in enumerate(game.mainline_moves(), start=1):
        fen_before = board.fen()
        move_san = board.san(move)
        side_to_move = "white" if board.turn == chess.WHITE else "black"

        analysis_before = await pool.analyze(fen_before, depth=request.depth, multipv=3, time_limit=1.8)
        eval_before = _evaluation_to_cp(analysis_before["evaluation"])

        best_line = analysis_before["best_moves"][0] if analysis_before.get("best_moves") else None
        best_move_san = best_line["san"] if best_line else "(none)"
        best_move_uci = best_line["move"] if best_line else ""

        board.push(move)
        fen_after = board.fen()
        analysis_after = await pool.analyze(fen_after, depth=request.depth, multipv=1, time_limit=1.2)
        eval_after = _evaluation_to_cp(analysis_after["evaluation"])

        side_factor = 1.0 if side_to_move == "white" else -1.0
        cp_loss = max(0.0, (eval_before * side_factor) - (eval_after * side_factor))
        classification = classify_move(cp_loss)
        is_critical = classification in {"mistake", "blunder"}

        coaching_text: str | None = None
        if is_critical:
            concepts = extract_concepts(chess.Board(fen_before), analysis_before)
            for theme in concepts["strategic_themes"]:
                theme_counter[theme] += 1
            critical_moves.append(ply_index)
            try:
                coaching_result = await CoachingService.explain_position(
                    db=db,
                    fen=fen_before,
                    best_move=best_move_san,
                    pv_lines=analysis_before.get("best_moves", []),
                    user_move=move_san,
                    last_move=move_analyses[-1].move if move_analyses else None,
                    eval_before=eval_before,
                    eval_after=eval_after,
                    player_level="intermediate",
                )
                coaching_text = coaching_result["explanation"]
            except Exception:
                coaching_text = None

        if side_to_move == request.player_color:
            player_classifications[classification] += 1
            player_move_scores.append(_move_accuracy(cp_loss))

        move_analyses.append(
            ReviewMoveAnalysis(
                move_number=ply_index,
                move=move_san,
                fen_before=fen_before,
                fen_after=fen_after,
                evaluation_before=round(eval_before, 2),
                evaluation_after=round(eval_after, 2),
                classification=classification,
                best_move=best_move_uci if best_move_uci else best_move_san,
                is_critical=is_critical,
                coaching=coaching_text,
            )
        )

    accuracy = round(sum(player_move_scores) / max(len(player_move_scores), 1), 2)
    move_breakdown = ", ".join(f"{k}: {v}" for k, v in player_classifications.items()) or "no classified moves"
    critical_str = ", ".join(str(x) for x in critical_moves[:15]) or "none"
    top_themes = [theme for theme, _count in theme_counter.most_common(4)]
    themes_text = ", ".join(top_themes) if top_themes else "calculation discipline"

    summary_text = (
        "You kept playable positions often, but missed tactical accuracy in critical moments. "
        "Review your biggest eval swings and train blunder-check habits before every move."
    )
    try:
        summary_text = await llm_service.generate(
            system_prompt="You are a practical chess coach.",
            user_prompt=GAME_SUMMARY_PROMPT.format(
                color=request.player_color,
                accuracy=accuracy,
                move_breakdown=move_breakdown,
                critical_moves=critical_str,
                error_themes=themes_text,
            ),
            max_tokens=300,
        )
    except Exception:
        pass

    summary = ReviewSummary(
        accuracy=accuracy,
        move_classifications=dict(player_classifications),
        themes_to_improve=top_themes or ["calculation discipline"],
        overall_coaching=summary_text,
    )

    response_game_id = str(uuid.uuid4())
    status = "completed_unsaved"

    if current_user:
        db_game = Game(
            user_id=current_user.id,
            pgn=pgn_text,
            white_player=game.headers.get("White"),
            black_player=game.headers.get("Black"),
            player_color=request.player_color,
            result=game.headers.get("Result"),
            accuracy=accuracy,
            summary=summary.model_dump(),
            moves=[move.model_dump() for move in move_analyses],
            source=source,
            lichess_id=lichess_id,
        )
        db.add(db_game)
        await db.commit()
        await db.refresh(db_game)
        response_game_id = str(db_game.id)
        status = "saved"

    return ReviewResponse(
        game_id=response_game_id,
        status=status,
        summary=summary,
        moves=move_analyses,
    )


@router.get("/review/{game_id}", response_model=ReviewResponse)
async def get_review(
    game_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    try:
        game_uuid = uuid.UUID(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid game id") from exc

    game = await db.get(Game, game_uuid)
    if not game:
        raise HTTPException(status_code=404, detail="Review not found")

    summary = ReviewSummary.model_validate(game.summary) if game.summary else None
    moves = [ReviewMoveAnalysis.model_validate(m) for m in (game.moves or [])]

    return ReviewResponse(
        game_id=str(game.id),
        status="saved",
        summary=summary,
        moves=moves,
    )
