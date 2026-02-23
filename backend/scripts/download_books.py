"""Download public-domain chess books used by the RAG pipeline."""

import asyncio
from pathlib import Path

import httpx

from app.rag.ingest import BOOKS


async def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    books_dir = base_dir / "data" / "books"
    books_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for book in BOOKS:
            target = books_dir / book["filename"]
            if target.exists():
                print(f"Skipping {book['title']} (already downloaded)")
                continue
            print(f"Downloading {book['title']}...")
            response = await client.get(book["url"])
            response.raise_for_status()
            target.write_text(response.text, encoding="utf-8")
            print(f"Saved {target}")


if __name__ == "__main__":
    asyncio.run(main())
