"""Download public-domain chess books used by the RAG pipeline."""

import asyncio
from pathlib import Path

from app.rag.downloaders import download_archive_djvu, download_gutenberg, local_file_is_usable
from app.rag.sources import all_sources


async def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    books_dir = base_dir / "data" / "books"
    books_dir.mkdir(parents=True, exist_ok=True)

    sources = [src for src in all_sources(include_pdf=False) if src.get("type") in {"gutenberg", "archive"}]
    for source in sources:
        target_name = source.get("filename") or f"{source.get('title', 'book').lower().replace(' ', '_')}.txt"
        target = books_dir / target_name
        if local_file_is_usable(str(target)):
            print(f"Skipping {source['title']} (already downloaded)")
            continue

        print(f"Downloading {source['title']}...")
        if source.get("type") == "gutenberg":
            await download_gutenberg(source["url"], str(target))
        elif source.get("type") == "archive":
            await download_archive_djvu(source["url"], str(target))
        print(f"Saved {target}")


if __name__ == "__main__":
    asyncio.run(main())
