import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.database import Game, User
from app.models.schemas import GameDetail, GameListItem

router = APIRouter()


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
