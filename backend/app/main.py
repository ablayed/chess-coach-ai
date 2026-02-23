from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, coaching, games, review
from app.config import settings
from app.core.stockfish_pool import StockfishPool
from app.db.migrations import create_tables
from app.db.session import engine
from app.services.coaching_service import llm_service

stockfish_pool: StockfishPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global stockfish_pool
    await create_tables()
    stockfish_pool = StockfishPool(
        path=settings.STOCKFISH_PATH,
        pool_size=settings.STOCKFISH_POOL_SIZE,
        hash_mb=settings.STOCKFISH_HASH_MB,
        threads=settings.STOCKFISH_THREADS,
    )
    await stockfish_pool.start()
    app.state.stockfish_pool = stockfish_pool
    try:
        yield
    finally:
        if stockfish_pool:
            await stockfish_pool.stop()
        await llm_service.close()
        await engine.dispose()


app = FastAPI(
    title="ChessCoach AI",
    description="Chess coaching API with Stockfish + RAG + LLM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(coaching.router, prefix="/api/v1", tags=["coaching"])
app.include_router(review.router, prefix="/api/v1", tags=["review"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(games.router, prefix="/api/v1/games", tags=["games"])


@app.get("/health")
async def health() -> dict[str, int | str]:
    return {"status": "ok", "stockfish_pool_size": settings.STOCKFISH_POOL_SIZE}
