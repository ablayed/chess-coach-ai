"""Quick Stockfish connectivity test for local development."""

from __future__ import annotations

import asyncio
import shutil

import chess

async def main() -> None:
    from app.config import settings
    from app.core.stockfish_pool import StockfishPool

    path = settings.STOCKFISH_PATH or shutil.which("stockfish")
    if not path:
        print("Stockfish path not found. Set STOCKFISH_PATH in backend/.env")
        return
    print(f"Using Stockfish at: {path}")

    fen = chess.STARTING_FEN
    pool = StockfishPool(
        path=path,
        pool_size=1,
        hash_mb=min(settings.STOCKFISH_HASH_MB, 64),
        threads=settings.STOCKFISH_THREADS,
    )
    await pool.start()
    try:
        result = await pool.analyze(fen=fen, depth=14, multipv=3, time_limit=2.0)
        print("Top 3 lines from starting position:")
        for index, line in enumerate(result.get("best_moves", [])[:3], start=1):
            eval_data = line.get("evaluation", {})
            eval_type = eval_data.get("type", "cp")
            eval_value = eval_data.get("value", 0)
            pv_san = " ".join(line.get("pv_san", [])[:8])
            print(f"{index}. {line.get('san', '?')} | {eval_type} {eval_value} | {pv_san}")
        print("Stockfish is working!")
    finally:
        await pool.stop()


if __name__ == "__main__":
    asyncio.run(main())
