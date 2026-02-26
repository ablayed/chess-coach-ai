from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, coaching, games, review
from app.config import settings
from app.core.stockfish_pool import StockfishPool
from app.db.migrations import create_tables
from app.db.session import async_session, engine
from app.services.coaching_service import llm_service

stockfish_pool: StockfishPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global stockfish_pool
    await create_tables()
    stockfish_pool = None
    try:
        stockfish_pool = StockfishPool(
            path=settings.STOCKFISH_PATH,
            pool_size=settings.STOCKFISH_POOL_SIZE,
            hash_mb=settings.STOCKFISH_HASH_MB,
            threads=settings.STOCKFISH_THREADS,
        )
        await stockfish_pool.start()
        app.state.stockfish_pool = stockfish_pool
        print(f"Stockfish pool started ({settings.STOCKFISH_POOL_SIZE} engines) at: {settings.STOCKFISH_PATH}")
    except Exception as exc:  # noqa: BLE001
        print(f"Stockfish failed to start: {exc}")
        print("Analysis endpoints will remain unavailable until STOCKFISH_PATH is fixed.")
        app.state.stockfish_pool = None
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
async def health():
    sf_ok = getattr(app.state, "stockfish_pool", None) is not None
    db_ok = False
    try:
        from sqlalchemy import text

        async with async_session() as db:
            await db.execute(text("SELECT 1"))
            db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False

    chunks_count = 0
    try:
        from sqlalchemy import text

        async with async_session() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM book_chunks"))
            chunks_count = result.scalar() or 0
    except Exception:  # noqa: BLE001
        chunks_count = 0

    return {
        "status": "ok" if (sf_ok and db_ok) else "degraded",
        "stockfish": "ready" if sf_ok else "unavailable",
        "database": "connected" if db_ok else "disconnected",
        "rag_chunks": chunks_count,
        "llm_providers": {
            "groq": bool(settings.GROQ_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
            "openrouter": bool(settings.OPENROUTER_API_KEY),
        },
    }
