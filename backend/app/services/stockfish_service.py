from app.core.stockfish_pool import StockfishPool


class StockfishService:
    """Thin wrapper around StockfishPool for service-style use."""

    def __init__(self, pool: StockfishPool):
        self.pool = pool

    async def analyze_position(self, fen: str, depth: int = 20, num_lines: int = 3) -> dict:
        return await self.pool.analyze(fen=fen, depth=depth, multipv=num_lines)
