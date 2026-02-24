"""RAG ingestion pipeline for multi-source chess knowledge."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from sqlalchemy import text as text_sql

from app.db.session import async_session
from app.models.database import BookChunk
from app.rag.chunker import chunk_text
from app.rag.downloaders import (
    download_archive_djvu,
    download_gutenberg,
    download_lichess_puzzles,
    download_lichess_studies,
    download_wikibooks_category,
    download_wikipedia_category,
    download_wikipedia_pages,
    local_file_is_usable,
    read_local_text,
)
from app.rag.sources import all_sources
from app.services.rag_service import RAGService

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "books"
MIN_TEXT_CHARS = 500
DEFAULT_WIKI_MAX_PAGES = 250
DEFAULT_PUZZLE_ROWS = 80000


CONCEPT_KEYWORDS: dict[str, list[str]] = {
    # Positional concepts
    "center_control": ["center", "centre", "central", "d4", "e4", "d5", "e5", "central control"],
    "development": ["develop", "minor piece", "mobiliz", "get your pieces out", "piece development"],
    "king_safety": ["king safety", "castl", "king side attack", "king exposure", "king in the center"],
    "pawn_structure": [
        "pawn structure",
        "isolated pawn",
        "doubled pawn",
        "pawn chain",
        "backward pawn",
        "hanging pawn",
        "pawn island",
    ],
    "open_file": ["open file", "semi-open", "rook on the file", "file control", "half-open"],
    "outpost": ["outpost", "strong square", "hole in the position"],
    "bishop_pair": ["bishop pair", "two bishops", "opposite-colored bishop"],
    "space_advantage": ["space", "cramped", "space advantage", "restrict"],
    "piece_activity": ["active piece", "piece activity", "mobility", "centralize", "passive piece"],
    "weak_squares": ["weak square", "hole", "color complex", "dark square weakness", "light square weakness"],
    "prophylaxis": ["prophylaxis", "prophylactic", "prevent", "overprotect"],
    # Tactical motifs
    "pin": ["pin", "pinned", "pinning", "absolute pin", "relative pin"],
    "fork": ["fork", "double attack", "family check", "knight fork", "royal fork"],
    "skewer": ["skewer", "x-ray attack"],
    "discovered_attack": ["discovered attack", "discovered check", "double check"],
    "sacrifice": ["sacrifice", "sac", "exchange sacrifice", "positional sacrifice", "greek gift"],
    "deflection": ["deflection", "decoy", "lure"],
    "overloading": ["overloaded", "overworked", "double duty"],
    "zwischenzug": ["zwischenzug", "intermediate move", "in-between move", "intermezzo"],
    "zugzwang": ["zugzwang", "compulsion to move"],
    "checkmate_pattern": ["mate", "checkmate", "smothered mate", "back rank", "epaulette"],
    # Opening theory
    "opening_theory": [
        "opening",
        "gambit",
        "defence",
        "defense",
        "variation",
        "system",
        "sicilian",
        "french",
        "caro-kann",
        "ruy lopez",
        "italian",
        "english",
        "queen's gambit",
        "king's indian",
        "nimzo",
    ],
    # Endgame
    "endgame_technique": [
        "endgame",
        "end game",
        "king and pawn",
        "rook ending",
        "opposition",
        "lucena",
        "philidor position",
        "triangulation",
        "corresponding square",
        "pawn ending",
        "queen ending",
        "minor piece ending",
    ],
    "passed_pawn": [
        "passed pawn",
        "advance the pawn",
        "pawn promotion",
        "outside passed pawn",
        "connected passed pawn",
        "protected passed pawn",
    ],
    # General
    "tactics": ["combination", "tactic", "attack", "threat", "calculate", "variation"],
    "strategy": ["plan", "strategic", "long-term", "positional", "advantage", "imbalance"],
    "initiative": ["initiative", "tempo", "time", "dynamic", "momentum"],
}


def tag_concepts(text_chunk: str) -> list[str]:
    """Auto-detect chess concepts in a chunk of text."""
    text_lower = text_chunk.lower()
    found: list[str] = []
    for concept, keywords in CONCEPT_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            found.append(concept)
    return found


def _slugify(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return normalized.strip("_") or "unknown"


def _source_filepath(source: dict[str, Any]) -> Path:
    filename = source.get("filename")
    if not filename:
        filename_prefix = source.get("filename_prefix", _slugify(source.get("title", "source")))
        filename = f"{filename_prefix}.txt"
    return DATA_DIR / filename


def _build_metadata_tags(source: dict[str, Any]) -> list[str]:
    tags = [f"source_type_{_slugify(source.get('type'))}"]
    tags.append(f"source_title_{_slugify(source.get('title'))}")
    tags.append(f"author_{_slugify(source.get('author'))}")
    tags.append(f"level_{_slugify(source.get('level'))}")
    for topic in source.get("topics", []):
        tags.append(f"topic_{_slugify(topic)}")
    return tags


def _build_chunk_content(source: dict[str, Any], content: str) -> str:
    author = source.get("author", "Unknown")
    level = source.get("level", "all")
    topics = ", ".join(source.get("topics", []))
    metadata_prefix = (
        f"Source: {source.get('title', 'Unknown')}\n"
        f"Author: {author}\n"
        f"Level: {level}\n"
        f"Topics: {topics}\n\n"
    )
    return metadata_prefix + content.strip()


async def _source_chunk_count(title: str) -> int:
    async with async_session() as db:
        result = await db.execute(
            text_sql("SELECT COUNT(*) FROM book_chunks WHERE book_title = :title"),
            {"title": title},
        )
        count = result.scalar_one() or 0
        return int(count)


async def _load_source_text(
    source: dict[str, Any],
    filepath: Path,
    wiki_max_pages: int,
    puzzle_rows: int,
) -> str:
    if local_file_is_usable(str(filepath)):
        text = read_local_text(str(filepath))
        if len(text) >= MIN_TEXT_CHARS:
            print(f"    Reusing local file ({len(text)} chars)")
            return text

    source_type = source.get("type")
    if source_type == "gutenberg":
        return await download_gutenberg(source["url"], str(filepath))
    if source_type == "archive":
        return await download_archive_djvu(source["url"], str(filepath))
    if source_type == "wikipedia":
        pages = source.get("pages")
        if pages:
            return await download_wikipedia_pages(
                pages=pages,
                filepath=str(filepath),
                base_url=source.get("base_url", "https://en.wikipedia.org/w/api.php"),
            )
        if source.get("category"):
            return await download_wikipedia_category(
                category=source["category"],
                base_url=source.get("base_url", "https://en.wikipedia.org/w/api.php"),
                filepath=str(filepath),
                max_pages=wiki_max_pages,
            )
        raise RuntimeError("wikipedia_source_missing_pages_and_category")
    if source_type == "wikibooks":
        return await download_wikibooks_category(
            category=source["category"],
            base_url=source.get("base_url", "https://en.wikibooks.org/w/api.php"),
            filepath=str(filepath),
            max_pages=wiki_max_pages,
        )
    if source_type == "lichess_studies":
        return await download_lichess_studies(
            study_ids=source.get("sample_study_ids", []),
            filepath=str(filepath),
        )
    if source_type == "lichess_puzzles":
        return await download_lichess_puzzles(
            url=source["url"],
            filepath=str(filepath),
            max_rows=puzzle_rows,
        )
    raise RuntimeError(f"unknown_source_type:{source_type}")


async def ingest_all(
    force_reprocess: bool = False,
    include_pdf: bool = False,
    wiki_max_pages: int = DEFAULT_WIKI_MAX_PAGES,
    puzzle_rows: int = DEFAULT_PUZZLE_ROWS,
) -> dict[str, int]:
    """Ingest all configured sources and store embeddings in pgvector."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {
        "sources": 0,
        "chunks": 0,
        "embeddings": 0,
        "failures": 0,
        "skipped": 0,
    }

    all_configured_sources = all_sources(include_pdf=include_pdf)
    print(f"Starting ingestion for {len(all_configured_sources)} configured sources...")

    for index, source in enumerate(all_configured_sources, start=1):
        title = source.get("title", "Unknown source")
        priority = source.get("priority", "?")
        source_type = source.get("type", "unknown")
        filepath = _source_filepath(source)
        print(f"\n[{index}/{len(all_configured_sources)}] [{priority}] {title} ({source_type})")

        if source.get("format") == "pdf" and not include_pdf:
            print("    Skipped (PDF source disabled)")
            stats["skipped"] += 1
            continue

        try:
            existing_chunks = await _source_chunk_count(title)
            if existing_chunks > 0 and not force_reprocess:
                print(f"    Skipped (already ingested with {existing_chunks} chunks)")
                stats["skipped"] += 1
                continue

            text = await _load_source_text(
                source=source,
                filepath=filepath,
                wiki_max_pages=wiki_max_pages,
                puzzle_rows=puzzle_rows,
            )
            if len(text) < MIN_TEXT_CHARS:
                print(f"    Text too short ({len(text)} chars), skipping")
                stats["failures"] += 1
                continue

            chunks = chunk_text(text, max_tokens=600, overlap_tokens=100)
            if not chunks:
                print("    No chunks generated, skipping")
                stats["failures"] += 1
                continue
            print(f"    Generated {len(chunks)} chunks")

            source_tags = _build_metadata_tags(source)
            inserted_count = 0

            async with async_session() as db:
                if existing_chunks > 0:
                    await db.execute(
                        text_sql("DELETE FROM book_chunks WHERE book_title = :title"),
                        {"title": title},
                    )

                batch: list[BookChunk] = []
                for chunk in chunks:
                    raw_content = chunk.get("content", "").strip()
                    if len(raw_content) < 50:
                        continue

                    concept_tags = tag_concepts(raw_content)
                    all_tags = sorted(set(concept_tags + source_tags))
                    content_with_metadata = _build_chunk_content(source, raw_content)
                    embedding = RAGService.embed(content_with_metadata)

                    batch.append(
                        BookChunk(
                            book_title=title,
                            chapter=chunk.get("chapter"),
                            section=chunk.get("section"),
                            content=content_with_metadata,
                            content_tokens=len(content_with_metadata.split()),
                            concepts=all_tags if all_tags else None,
                            embedding=embedding,
                        )
                    )

                    if len(batch) >= 50:
                        db.add_all(batch)
                        await db.flush()
                        inserted_count += len(batch)
                        stats["embeddings"] += len(batch)
                        batch = []

                if batch:
                    db.add_all(batch)
                    await db.flush()
                    inserted_count += len(batch)
                    stats["embeddings"] += len(batch)

                await db.commit()

            stats["sources"] += 1
            stats["chunks"] += inserted_count
            print(f"    Stored {inserted_count} chunks")

        except Exception as exc:  # noqa: BLE001
            print(f"    FAILED: {exc}")
            stats["failures"] += 1
            continue

    print("\nIngestion finished.")
    print(
        "Summary: "
        f"sources={stats['sources']}, chunks={stats['chunks']}, "
        f"embeddings={stats['embeddings']}, skipped={stats['skipped']}, failures={stats['failures']}"
    )
    return stats


async def ingest() -> None:
    """Backward-compatible entrypoint used by scripts/run_ingestion.py."""
    await ingest_all()


if __name__ == "__main__":
    asyncio.run(ingest_all())
