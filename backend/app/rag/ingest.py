"""
RAG Ingestion Pipeline
Run: python -m app.rag.ingest

Downloads public domain chess books, chunks them, embeds, and stores in pgvector.
"""

import asyncio
import os
from pathlib import Path

import httpx
from sqlalchemy import text

from app.db.session import async_session
from app.models.database import BookChunk
from app.rag.chunker import chunk_text
from app.services.rag_service import RAGService

BOOKS = [
    {
        "title": "Chess Fundamentals",
        "author": "Jose Raul Capablanca",
        "year": 1921,
        "url": "https://www.gutenberg.org/cache/epub/33870/pg33870.txt",
        "filename": "chess_fundamentals.txt",
    },
    {
        "title": "Chess Strategy",
        "author": "Edward Lasker",
        "year": 1915,
        "url": "https://www.gutenberg.org/cache/epub/5614/pg5614.txt",
        "filename": "chess_strategy.txt",
    },
]

CHESS_CONCEPTS = [
    "center_control",
    "development",
    "king_safety",
    "pawn_structure",
    "open_file",
    "bishop_pair",
    "outpost",
    "pin",
    "fork",
    "skewer",
    "discovered_attack",
    "passed_pawn",
    "endgame_technique",
    "opening_theory",
    "sacrifice",
    "initiative",
    "space_advantage",
    "piece_activity",
    "weak_squares",
    "prophylaxis",
]


def tag_concepts(text_chunk: str) -> list[str]:
    """Auto-detect chess concepts in a chunk of text."""
    text_lower = text_chunk.lower()
    found: list[str] = []
    keyword_map = {
        "center_control": ["center", "centre", "central"],
        "development": ["develop", "piece development", "castl"],
        "king_safety": ["king safety", "castl", "attack on king"],
        "pawn_structure": ["pawn structure", "isolated pawn", "doubled pawn", "pawn chain"],
        "open_file": ["open file", "semi-open", "rook on file"],
        "bishop_pair": ["bishop pair", "two bishops"],
        "pin": ["pin", "pinned"],
        "fork": ["fork", "double attack"],
        "passed_pawn": ["passed pawn", "advance pawn"],
        "endgame_technique": ["endgame", "end game", "king and pawn"],
        "opening_theory": ["opening", "gambit", "defense", "variation"],
        "sacrifice": ["sacrifice", "sac"],
        "piece_activity": ["active", "piece activity", "mobility"],
    }
    for concept, keywords in keyword_map.items():
        if any(keyword in text_lower for keyword in keywords):
            found.append(concept)
    return found


async def ingest() -> None:
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = base_dir / "data" / "books"
    data_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for book in BOOKS:
            filepath = data_dir / book["filename"]
            if not filepath.exists():
                print(f"Downloading {book['title']}...")
                resp = await client.get(book["url"])
                resp.raise_for_status()
                filepath.write_text(resp.text, encoding="utf-8")

            print(f"Processing {book['title']}...")
            raw_text = filepath.read_text(encoding="utf-8")

            start_marker = "*** START OF"
            end_marker = "*** END OF"
            start_idx = raw_text.find(start_marker)
            end_idx = raw_text.find(end_marker)
            if start_idx > 0:
                raw_text = raw_text[raw_text.index("\n", start_idx) + 1 :]
            if end_idx > 0:
                raw_text = raw_text[:end_idx]

            chunks = chunk_text(raw_text, max_tokens=600, overlap_tokens=100)
            print(f"  Generated {len(chunks)} chunks")

            async with async_session() as db:
                await db.execute(
                    text("DELETE FROM book_chunks WHERE book_title = :title"),
                    {"title": book["title"]},
                )

                for chunk in chunks:
                    concepts = tag_concepts(chunk["content"])
                    embedding = RAGService.embed(chunk["content"])
                    db_chunk = BookChunk(
                        book_title=book["title"],
                        chapter=chunk.get("chapter"),
                        section=chunk.get("section"),
                        content=chunk["content"],
                        content_tokens=chunk.get("tokens", len(chunk["content"].split())),
                        concepts=concepts if concepts else None,
                        embedding=embedding,
                    )
                    db.add(db_chunk)

                await db.commit()
                print(f"  Stored {len(chunks)} chunks for {book['title']}")

    print("Ingestion complete!")


if __name__ == "__main__":
    asyncio.run(ingest())
