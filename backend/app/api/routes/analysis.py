import hashlib
import json

import chess
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_stockfish_pool
from app.core.concept_extractor import extract_concepts
from app.core.stockfish_pool import StockfishPool
from app.db.session import get_db
from app.models.database import AnalysisCache
from app.models.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter()


def _fen_hash(fen: str) -> str:
    return hashlib.sha256(fen.encode("utf-8")).hexdigest()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_position(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    pool: StockfishPool = Depends(get_stockfish_pool),
) -> AnalyzeResponse:
    try:
        board = chess.Board(request.fen)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid FEN") from exc

    fen = board.fen()
    fen_hash = _fen_hash(fen)
    cached = await db.get(AnalysisCache, fen_hash)

    stockfish_result: dict
    if (
        cached
        and cached.stockfish_result
        and cached.depth is not None
        and cached.depth >= request.depth
        and cached.fen == fen
    ):
        cached.hit_count += 1
        await db.commit()
        stockfish_result = cached.stockfish_result
    else:
        stockfish_result = await pool.analyze(
            fen=fen,
            depth=request.depth,
            multipv=request.num_lines,
            time_limit=6.0,
        )
        if cached:
            cached.stockfish_result = stockfish_result
            cached.depth = request.depth
            cached.fen = fen
        else:
            cached = AnalysisCache(
                fen_hash=fen_hash,
                fen=fen,
                stockfish_result=stockfish_result,
                depth=request.depth,
                hit_count=0,
            )
            db.add(cached)
        await db.commit()

    concepts = extract_concepts(board, stockfish_result)

    response_payload = {
        "fen": fen,
        "evaluation": stockfish_result.get("evaluation", {"type": "cp", "value": 0, "wdl": None}),
        "best_moves": stockfish_result.get("best_moves", []),
        "position_concepts": concepts,
    }
    return AnalyzeResponse.model_validate(response_payload)


@router.get("/analyze/stream")
async def analyze_stream(
    fen: str = Query(...),
    depth: int = Query(20, ge=8, le=40),
    pool: StockfishPool = Depends(get_stockfish_pool),
) -> StreamingResponse:
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid FEN") from exc

    normalized_fen = board.fen()

    async def event_generator():
        yield "retry: 2500\n\n"
        async for payload in pool.analyze_stream(normalized_fen, depth=depth):
            yield f"data: {json.dumps(payload)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
