"""Run the full ingestion pipeline from scripts/."""

import asyncio

from app.rag.ingest import ingest_all


if __name__ == "__main__":
    result = asyncio.run(ingest_all())
    print(result)
