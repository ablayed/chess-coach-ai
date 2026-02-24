"""Run and verify the RAG ingestion pipeline."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure imports work when invoked as `python -m scripts.run_ingestion`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main() -> None:
    print("=" * 60)
    print("ChessCoach AI - RAG Ingestion Pipeline")
    print("=" * 60)

    print("\nStep 1: Downloading public domain chess books...")
    from app.rag.ingest import download_books, ingest_all

    download_stats = await download_books()
    print(
        f"Download summary: downloaded={download_stats['downloaded']}, "
        f"skipped={download_stats['skipped']}, failures={download_stats['failures']}"
    )

    print("\nStep 2: Processing chunks + embeddings + pgvector...")
    stats = await ingest_all()
    print("\nIngestion complete!")
    print(f"  Books processed: {stats.get('books', stats.get('sources', 0))}")
    print(f"  Total chunks: {stats.get('chunks', 0)}")
    print(f"  Embeddings stored: {stats.get('embeddings', 0)}")
    print(f"  Failures: {stats.get('failures', 0)}")

    print("\nStep 3: Testing retrieval...")
    from app.db.session import async_session
    from app.services.rag_service import RAGService

    test_queries = [
        "controlling the center in the opening",
        "rook endgame technique",
        "knight fork tactics",
        "pawn structure weaknesses",
    ]

    async with async_session() as db:
        for query in test_queries:
            results = await RAGService.retrieve(db=db, query=query, top_k=2)
            print(f"\nQuery: '{query}'")
            if results:
                for item in results:
                    preview = item["content"][:80].replace("\n", " ")
                    print(f"  [{item['relevance_score']:.3f}] {item['source']}: {preview}...")
            else:
                print("  No results found")

    print("\nRAG pipeline is working!")


if __name__ == "__main__":
    asyncio.run(main())
