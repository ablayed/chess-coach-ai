import uuid
import io
import re
from urllib.parse import urlparse

import chess.pgn
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.database import Game, User
from app.models.schemas import GameDetail, GameListItem, SaveGameRequest

router = APIRouter()


def _extract_lichess_game_id(url: str) -> str | None:
    raw = url.strip()
    if not raw:
        return None

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    if "lichess.org" not in parsed.netloc:
        return None

    parts = [part for part in parsed.path.rstrip("/").split("/") if part]
    if not parts:
        return None

    game_id = parts[-1]
    if game_id in {"white", "black"} and len(parts) >= 2:
        game_id = parts[-2]
    game_id = game_id.split("?")[0]

    if not re.match(r"^[A-Za-z0-9]{8,12}$", game_id):
        return None
    return game_id


@router.post("", response_model=GameDetail)
async def save_game(
    request: SaveGameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameDetail:
    parsed_game = chess.pgn.read_game(io.StringIO(request.pgn))
    if parsed_game is None:
        raise HTTPException(status_code=400, detail="Invalid PGN")

    lichess_id = _extract_lichess_game_id(request.lichess_url or "") if request.lichess_url else None
    source = "lichess" if lichess_id else "pgn_import"

    db_game = Game(
        user_id=current_user.id,
        pgn=request.pgn,
        white_player=parsed_game.headers.get("White"),
        black_player=parsed_game.headers.get("Black"),
        player_color=request.player_color,
        result=parsed_game.headers.get("Result"),
        accuracy=request.summary.accuracy if request.summary else None,
        summary=request.summary.model_dump() if request.summary else None,
        moves=[move.model_dump() for move in request.moves] if request.moves else None,
        source=source,
        lichess_id=lichess_id,
    )
    db.add(db_game)
    await db.commit()
    await db.refresh(db_game)

    return GameDetail.model_validate(
        {
            "id": str(db_game.id),
            "pgn": db_game.pgn,
            "white_player": db_game.white_player,
            "black_player": db_game.black_player,
            "player_color": db_game.player_color,
            "result": db_game.result,
            "accuracy": db_game.accuracy,
            "summary": db_game.summary,
            "moves": db_game.moves,
            "source": db_game.source,
            "lichess_id": db_game.lichess_id,
            "created_at": db_game.created_at,
        }
    )


@router.get("", response_model=list[GameListItem])
async def list_games(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GameListItem]:
    result = await db.execute(
        select(Game)
        .where(Game.user_id == current_user.id)
        .order_by(Game.created_at.desc())
    )
    games = result.scalars().all()
    return [
        GameListItem.model_validate(
            {
                "id": str(g.id),
                "white_player": g.white_player,
                "black_player": g.black_player,
                "result": g.result,
                "accuracy": g.accuracy,
                "created_at": g.created_at,
            }
        )
        for g in games
    ]


@router.get("/{game_id}", response_model=GameDetail)
async def get_game(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameDetail:
    try:
        game_uuid = uuid.UUID(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid game id") from exc

    game = await db.get(Game, game_uuid)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return GameDetail.model_validate(
        {
            "id": str(game.id),
            "pgn": game.pgn,
            "white_player": game.white_player,
            "black_player": game.black_player,
            "player_color": game.player_color,
            "result": game.result,
            "accuracy": game.accuracy,
            "summary": game.summary,
            "moves": game.moves,
            "source": game.source,
            "lichess_id": game.lichess_id,
            "created_at": game.created_at,
        }
    )


@router.delete("/{game_id}")
async def delete_game(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        game_uuid = uuid.UUID(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid game id") from exc

    game = await db.get(Game, game_uuid)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await db.delete(game)
    await db.commit()
    return {"status": "deleted"}
