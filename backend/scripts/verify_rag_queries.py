"""Run standard RAG verification prompts against stored book chunks."""

from __future__ import annotations

import asyncio

from app.db.session import async_session
from app.services.rag_service import RAGService

TEST_QUERIES = [
    "how to control the center in the opening",
    "rook endgame technique lucena position",
    "knight fork tactical pattern",
    "nimzowitsch prophylaxis overprotection",
    "sicilian defense najdorf variation ideas",
    "passed pawn endgame winning technique",
    "bishop pair advantage in open positions",
    "king safety castling principles",
]


async def main() -> None:
    async with async_session() as db:
        for query in TEST_QUERIES:
            print(f"\nQuery: {query}")
            rows = await RAGService.retrieve(db=db, query=query, top_k=3)
            if not rows:
                print("  No results.")
                continue
            for i, row in enumerate(rows, start=1):
                source = row.get("source", "Unknown")
                score = row.get("relevance_score", 0)
                content = (row.get("content", "") or "").replace("\n", " ")
                preview = content[:220].strip()
                print(f"  {i}. [{score}] {source}")
                print(f"     {preview}")


if __name__ == "__main__":
    asyncio.run(main())
