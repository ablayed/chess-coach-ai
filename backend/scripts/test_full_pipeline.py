"""
Full integration test:
Position -> Stockfish -> Concepts -> RAG -> LLM Coaching.
"""

from __future__ import annotations

import asyncio

import chess

from app.config import settings
from app.core.concept_extractor import extract_concepts
from app.core.stockfish_pool import StockfishPool
from app.db.session import async_session
from app.services.coaching_service import CoachingService
from app.services.rag_service import RAGService


async def test() -> None:
    print("=" * 60)
    print("ChessCoach AI - Full Pipeline Integration Test")
    print("=" * 60)

    print("\nStep 1: Stockfish Analysis")
    pool = StockfishPool(
        path=settings.STOCKFISH_PATH,
        pool_size=1,
        hash_mb=64,
        threads=1,
    )
    await pool.start()

    test_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    print(f"FEN: {test_fen}")
    analysis = await pool.analyze(test_fen, depth=18, multipv=3)
    print(f"Evaluation: {analysis['evaluation']}")
    for line in analysis.get("best_moves", [])[:3]:
        print(f"  {line['san']} (eval: {line['evaluation']})")
    await pool.stop()
    print("Stockfish OK")

    print("\nStep 2: Concept Extraction")
    board = chess.Board(test_fen)
    concepts = extract_concepts(board, analysis)
    print(f"Phase: {concepts['phase']}")
    print(f"Tactical motifs: {concepts['tactical_motifs']}")
    print(f"Strategic themes: {concepts['strategic_themes']}")
    print(f"King safety: {concepts['king_safety']}")
    print("Concepts OK")

    print("\nStep 3: RAG Retrieval")
    rag_query = f"{concepts['phase']} {' '.join(concepts['strategic_themes'])}".strip()
    print(f"Query: '{rag_query}'")
    async with async_session() as db:
        passages = await RAGService.retrieve(db, rag_query, top_k=3)
    if passages:
        for p in passages:
            preview = p["content"][:80].replace("\n", " ")
            print(f"  [{p['relevance_score']:.3f}] {p['source']}: {preview}...")
        print("RAG OK")
    else:
        print("No passages found - run ingestion first: python -m scripts.run_ingestion")

    print("\nStep 4: LLM Coaching Explanation")
    best_move = analysis["best_moves"][0]
    async with async_session() as db:
        result = await CoachingService.explain_position(
            db=db,
            fen=test_fen,
            best_move=best_move["san"],
            pv_lines=analysis["best_moves"],
            user_move="Nf6",
            eval_before=0,
            eval_after=analysis["evaluation"].get("value", 0),
            player_level="intermediate",
        )

    print("\nCoaching explanation:\n")
    print(result["explanation"])
    print(f"\nMove classification: {result['move_classification']}")
    print(f"Key concepts: {result['key_concepts']}")
    if result.get("book_references"):
        print("Book references:")
        for ref in result["book_references"]:
            print(f"  - {ref['source']} (relevance: {ref['relevance_score']})")

    print("\n" + "=" * 60)
    print("FULL PIPELINE IS WORKING!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test())
