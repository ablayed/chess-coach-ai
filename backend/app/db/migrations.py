from sqlalchemy import text

from app.db.session import engine
from app.models.database import Base


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
