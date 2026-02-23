from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag_service import RAGService


async def retrieve_similar_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 3,
    concepts: list[str] | None = None,
) -> list[dict]:
    """Retrieve similar chunks through the main RAG service."""
    return await RAGService.retrieve(db=db, query=query, top_k=top_k, concepts=concepts)
