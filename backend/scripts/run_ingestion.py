"""Run the full ingestion pipeline from scripts/."""

import asyncio

from app.rag.ingest import ingest


if __name__ == "__main__":
    asyncio.run(ingest())
