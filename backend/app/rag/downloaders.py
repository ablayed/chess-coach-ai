"""Download handlers for chess RAG sources."""

from __future__ import annotations

import asyncio
import csv
import io
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx

USER_AGENT = "ChessCoachAI-RAGIngest/1.0 (+https://github.com/)"


def _write_text(filepath: str, text: str) -> None:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def _strip_gutenberg_boilerplate(text: str) -> str:
    lines = text.splitlines()
    start_idx = 0
    end_idx = len(lines)

    for i, line in enumerate(lines):
        line_upper = line.upper()
        if "*** START OF" in line_upper or "***START OF" in line_upper:
            start_idx = i + 1
            break

    for i in range(len(lines) - 1, -1, -1):
        line_upper = lines[i].upper()
        if "*** END OF" in line_upper or "***END OF" in line_upper:
            end_idx = i
            break

    return "\n".join(lines[start_idx:end_idx]).strip()


def _cleanup_archive_ocr(text: str) -> str:
    # Normalize line endings first.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove isolated page number lines.
    text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)
    # Collapse repeated whitespace artifacts.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def download_gutenberg(url: str, filepath: str) -> str:
    """Download a Project Gutenberg text file and strip header/footer."""
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        text = response.text

    cleaned = _strip_gutenberg_boilerplate(text)
    _write_text(filepath, cleaned)
    return cleaned


async def download_archive_djvu(url: str, filepath: str) -> str:
    """Download OCR/DjVu text from Archive.org."""
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": USER_AGENT})
        if response.status_code != 200:
            raise RuntimeError(f"archive_download_failed:{response.status_code}")
        text = response.text

    cleaned = _cleanup_archive_ocr(text)
    _write_text(filepath, cleaned)
    return cleaned


async def _fetch_category_titles(
    client: httpx.AsyncClient,
    base_url: str,
    category: str,
    max_pages: int,
    delay_seconds: float,
) -> list[str]:
    titles: list[str] = []
    continuation: str | None = None

    while len(titles) < max_pages:
        params: dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": 50,
            "cmtype": "page",
            "format": "json",
        }
        if continuation:
            params["cmcontinue"] = continuation

        response = await client.get(base_url, params=params)
        response.raise_for_status()
        payload = response.json()
        members = payload.get("query", {}).get("categorymembers", [])
        titles.extend(member.get("title", "") for member in members if member.get("title"))

        cont = payload.get("continue", {})
        continuation = cont.get("cmcontinue")
        if not continuation:
            break
        await asyncio.sleep(delay_seconds)

    return titles[:max_pages]


async def _fetch_extract(
    client: httpx.AsyncClient,
    base_url: str,
    title: str,
) -> tuple[str, str]:
    response = await client.get(
        base_url,
        params={
            "action": "query",
            "titles": unquote(title).replace("_", " "),
            "prop": "extracts",
            "explaintext": True,
            "format": "json",
        },
    )
    response.raise_for_status()
    payload = response.json()
    pages = payload.get("query", {}).get("pages", {})
    for page_id, page_data in pages.items():
        if page_id == "-1":
            continue
        page_title = page_data.get("title", title)
        extract = page_data.get("extract", "")
        return page_title, extract
    return title, ""


async def _download_mediawiki_titles(
    titles: list[str],
    filepath: str,
    base_url: str,
    delay_seconds: float = 0.5,
    min_extract_chars: int = 120,
) -> str:
    all_parts: list[str] = []
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        for index, title in enumerate(titles):
            try:
                page_title, extract = await _fetch_extract(client, base_url=base_url, title=title)
                if extract and len(extract) >= min_extract_chars:
                    all_parts.append(f"## {page_title}\n\n{extract.strip()}")
            except Exception as exc:  # noqa: BLE001
                print(f"     Failed to fetch page '{title}': {exc}")

            if index < len(titles) - 1:
                await asyncio.sleep(delay_seconds)

    text = "\n\n".join(all_parts).strip()
    _write_text(filepath, text)
    return text


async def download_wikipedia_pages(
    pages: list[str],
    filepath: str,
    base_url: str = "https://en.wikipedia.org/w/api.php",
    delay_seconds: float = 0.5,
) -> str:
    """Download specific Wikipedia pages as plain text extracts."""
    return await _download_mediawiki_titles(
        titles=pages,
        filepath=filepath,
        base_url=base_url,
        delay_seconds=delay_seconds,
        min_extract_chars=200,
    )


async def download_wikipedia_category(
    category: str,
    base_url: str,
    filepath: str,
    max_pages: int = 300,
    delay_seconds: float = 0.5,
) -> str:
    """Download pages from a Wikipedia category and combine extracts."""
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        titles = await _fetch_category_titles(
            client=client,
            base_url=base_url,
            category=category,
            max_pages=max_pages,
            delay_seconds=delay_seconds,
        )
    print(f"    Found {len(titles)} pages in category {category}")
    return await _download_mediawiki_titles(
        titles=titles,
        filepath=filepath,
        base_url=base_url,
        delay_seconds=delay_seconds,
        min_extract_chars=120,
    )


async def download_wikibooks_category(
    category: str,
    base_url: str,
    filepath: str,
    max_pages: int = 250,
    delay_seconds: float = 0.5,
) -> str:
    """Download pages from a Wikibooks category and combine extracts."""
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        titles = await _fetch_category_titles(
            client=client,
            base_url=base_url,
            category=category,
            max_pages=max_pages,
            delay_seconds=delay_seconds,
        )
    print(f"    Found {len(titles)} pages in category {category}")
    return await _download_mediawiki_titles(
        titles=titles,
        filepath=filepath,
        base_url=base_url,
        delay_seconds=delay_seconds,
        min_extract_chars=100,
    )


async def download_lichess_studies(
    study_ids: list[str],
    filepath: str,
    delay_seconds: float = 0.5,
) -> str:
    """Download Lichess studies and extract natural-language PGN comments."""
    sections: list[str] = []
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"Accept": "application/x-chess-pgn", "User-Agent": USER_AGENT},
    ) as client:
        for index, study_id in enumerate(study_ids):
            try:
                response = await client.get(f"https://lichess.org/api/study/{study_id}.pgn")
                response.raise_for_status()
                pgn_text = response.text
                comments = re.findall(r"\{([^}]+)\}", pgn_text)
                cleaned_comments = [comment.strip() for comment in comments if len(comment.strip()) >= 20]
                if cleaned_comments:
                    sections.append(f"## Lichess Study {study_id}\n\n" + "\n".join(cleaned_comments))
            except Exception as exc:  # noqa: BLE001
                print(f"     Failed to fetch study {study_id}: {exc}")

            if index < len(study_ids) - 1:
                await asyncio.sleep(delay_seconds)

    text = "\n\n".join(sections).strip()
    _write_text(filepath, text)
    return text


async def download_lichess_puzzles(
    url: str,
    filepath: str,
    max_rows: int = 100000,
) -> str:
    """
    Download Lichess puzzles and generate NL coaching snippets from themes/moves.

    The source is distributed as zstd-compressed CSV. This function stores the raw
    archive next to the rendered text and returns generated instructional text.
    """
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_zst_path = output_path.with_suffix(output_path.suffix + ".zst")

    if not raw_zst_path.exists() or raw_zst_path.stat().st_size < 1024:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            raw_zst_path.write_bytes(response.content)

    try:
        import zstandard  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "zstandard package is required to parse lichess puzzles (pip install zstandard)"
        ) from exc

    generated_lines: list[str] = []
    with raw_zst_path.open("rb") as compressed_stream:
        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(compressed_stream) as reader:
            text_stream = io.TextIOWrapper(reader, encoding="utf-8")
            csv_reader = csv.DictReader(text_stream)

            for row_index, row in enumerate(csv_reader):
                if row_index >= max_rows:
                    break
                moves = (row.get("Moves") or "").split()
                first_move = moves[0] if moves else "best move"
                themes = (row.get("Themes") or "").replace("_", " ")
                rating = row.get("Rating", "?")
                fen = row.get("FEN", "")
                puzzle_id = row.get("PuzzleId", "")
                opening_tags = row.get("OpeningTags", "")
                line = (
                    f"Puzzle {puzzle_id}: rating {rating}. Themes: {themes}. "
                    f"In FEN {fen}, the key move is {first_move}. "
                    f"Opening context: {opening_tags}."
                )
                generated_lines.append(line)

    text = "\n".join(generated_lines).strip()
    _write_text(filepath, text)
    return text


def read_local_text(filepath: str) -> str:
    """Read an existing local source file with robust decoding."""
    path = Path(filepath)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def local_file_is_usable(filepath: str, min_bytes: int = 256) -> bool:
    """Quick check for an already downloaded local source file."""
    return os.path.exists(filepath) and os.path.getsize(filepath) >= min_bytes
