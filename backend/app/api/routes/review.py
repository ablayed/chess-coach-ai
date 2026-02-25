import io
import re
import uuid
from collections import Counter
from urllib.parse import urlparse

import chess
import chess.pgn
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_stockfish_pool
from app.core.concept_extractor import classify_move, extract_concepts
from app.core.prompt_templates import GAME_SUMMARY_PROMPT
from app.core.stockfish_pool import StockfishPool
from app.db.session import get_db
from app.models.database import Game
from app.models.schemas import ReviewMoveAnalysis, ReviewRequest, ReviewResponse, ReviewSummary
from app.services.coaching_service import CoachingService, llm_service

router = APIRouter()


def _extract_lichess_game_id(url: str) -> str:
    raw = url.strip()
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")

    if "lichess.org" not in parsed.netloc:
        raise ValueError("URL is not a lichess.org link")

    parts = [part for part in parsed.path.rstrip("/").split("/") if part]
    if not parts:
        raise ValueError("Invalid Lichess URL")

    game_id = parts[-1]
    if game_id in {"white", "black"} and len(parts) >= 2:
        game_id = parts[-2]
    game_id = game_id.split("?")[0]

    if not re.match(r"^[A-Za-z0-9]{8,12}$", game_id):
        raise ValueError(f"Invalid Lichess game ID: {game_id}")
    return game_id


async def fetch_lichess_pgn(url: str) -> str:
    """Extract Lichess game ID from URL and return exported PGN text."""
    game_id = _extract_lichess_game_id(url)
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(
            f"https://lichess.org/game/export/{game_id}",
            headers={"Accept": "application/x-chess-pgn"},
        )
        if response.status_code != 200:
            raise ValueError(f"Could not fetch game from Lichess (status {response.status_code})")
        pgn = response.text.strip()
        if not pgn:
            raise ValueError("Empty PGN from Lichess")
        return pgn


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
) -> ReviewResponse:
    pgn_text = request.pgn

    if request.lichess_url:
        try:
            _extract_lichess_game_id(request.lichess_url)
            pgn_text = await fetch_lichess_pgn(request.lichess_url)
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

    return ReviewResponse(
        game_id=str(uuid.uuid4()),
        status="completed_unsaved",
        player_color=request.player_color,
        pgn=pgn_text,
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
        player_color=game.player_color if game.player_color in {"white", "black"} else "white",
        pgn=game.pgn,
        summary=summary,
        moves=moves,
    )
