import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import chess
import chess.engine


class StockfishPool:
    """Manages a pool of Stockfish UCI engine processes."""

    def __init__(self, path: str, pool_size: int = 2, hash_mb: int = 128, threads: int = 1):
        self.path = path
        self.pool_size = pool_size
        self.hash_mb = hash_mb
        self.threads = threads
        self._queue: asyncio.Queue[chess.engine.UciProtocol] = asyncio.Queue()
        self._engines: list[chess.engine.UciProtocol] = []

    async def start(self) -> None:
        """Initialize all Stockfish processes."""
        for _ in range(self.pool_size):
            _transport, engine = await chess.engine.popen_uci(self.path)
            await engine.configure({"Hash": self.hash_mb, "Threads": self.threads})
            self._engines.append(engine)
            self._queue.put_nowait(engine)

    async def stop(self) -> None:
        """Gracefully shut down all engines."""
        for eng in self._engines:
            try:
                await eng.quit()
            except Exception:
                eng.close()
        self._engines.clear()

    async def analyze(
        self,
        fen: str,
        depth: int = 20,
        multipv: int = 3,
        time_limit: float = 10.0,
    ) -> dict[str, Any]:
        """Analyze a position. Returns eval + best moves + PV lines."""
        engine = await asyncio.wait_for(self._queue.get(), timeout=30.0)
        try:
            board = chess.Board(fen)
            limit = chess.engine.Limit(depth=depth, time=time_limit)
            raw_results = await engine.analyse(board, limit, multipv=multipv)
            results = raw_results if isinstance(raw_results, list) else [raw_results]

            best_moves: list[dict[str, Any]] = []
            for info in results:
                score = info.get("score")
                pv = info.get("pv", [])
                if not score or not pv:
                    continue

                pv_san: list[str] = []
                temp_board = board.copy()
                for pv_move in pv:
                    pv_san.append(temp_board.san(pv_move))
                    temp_board.push(pv_move)

                white_score = score.white()
                cp = white_score.score(mate_score=10000)
                is_mate = white_score.is_mate()
                mate_val = white_score.mate()

                best_moves.append(
                    {
                        "move": pv[0].uci(),
                        "san": board.san(pv[0]),
                        "evaluation": {
                            "type": "mate" if is_mate else "cp",
                            "value": mate_val if is_mate and mate_val is not None else (cp or 0),
                        },
                        "pv": [m.uci() for m in pv],
                        "pv_san": pv_san,
                        "depth": info.get("depth", depth),
                    }
                )

            wdl: tuple[int, int, int] | None = None
            if results and "wdl" in results[0]:
                raw_wdl = results[0]["wdl"]
                if hasattr(raw_wdl, "relative"):
                    relative = raw_wdl.relative
                    wdl = (int(relative.wins), int(relative.draws), int(relative.losses))
                elif isinstance(raw_wdl, tuple):
                    wdl = (int(raw_wdl[0]), int(raw_wdl[1]), int(raw_wdl[2]))

            top_eval = best_moves[0]["evaluation"] if best_moves else {"type": "cp", "value": 0}
            return {
                "fen": fen,
                "evaluation": {**top_eval, "wdl": wdl},
                "best_moves": best_moves,
                "depth": depth,
            }
        finally:
            self._queue.put_nowait(engine)

    async def analyze_stream(self, fen: str, depth: int = 20) -> AsyncGenerator[dict[str, Any], None]:
        """Yield analysis snapshots for SSE streaming."""
        engine = await asyncio.wait_for(self._queue.get(), timeout=30.0)
        try:
            board = chess.Board(fen)
            analysis = await engine.analysis(board, chess.engine.Limit(depth=depth), multipv=1)
            with analysis:
                async for info in analysis:
                    current_depth = int(info.get("depth", 0))
                    score = info.get("score")
                    pv = info.get("pv", [])
                    if score and pv and current_depth >= 5 and current_depth % 5 == 0:
                        white_score = score.white()
                        cp = white_score.score(mate_score=10000)
                        is_mate = white_score.is_mate()
                        mate_val = white_score.mate()
                        yield {
                            "depth": current_depth,
                            "evaluation": {
                                "type": "mate" if is_mate else "cp",
                                "value": mate_val if is_mate and mate_val is not None else (cp or 0),
                            },
                            "best_move": pv[0].uci(),
                            "best_move_san": board.san(pv[0]),
                            "pv": [m.uci() for m in pv[:5]],
                            "nodes": int(info.get("nodes", 0)),
                        }
                    if current_depth >= depth:
                        break
        finally:
            self._queue.put_nowait(engine)
