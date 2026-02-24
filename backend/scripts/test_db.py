"""Test database connection and schema readiness."""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.migrations import create_tables
from app.db.session import engine


async def test() -> None:
    print("Connecting to database...")
    try:
        await create_tables()
        print("Tables created successfully!")

        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in result]
            print(f"Tables found: {tables}")

            result = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("pgvector extension is active!")
            else:
                print("pgvector not found - run: CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception as exc:  # noqa: BLE001
        print(f"Database connection failed: {exc}")
        print("Check your DATABASE_URL in .env")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test())
