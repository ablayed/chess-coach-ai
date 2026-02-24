from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


class RAGService:
    """Retrieve relevant chess book passages from pgvector."""

    @staticmethod
    def _get_model() -> SentenceTransformer:
        global _model
        if _model is None:
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        return _model

    @staticmethod
    def embed(text_input: str) -> list[float]:
        return RAGService._get_model().encode(text_input).tolist()

    @staticmethod
    async def retrieve(
        db: AsyncSession,
        query: str,
        top_k: int = 3,
        concepts: list[str] | None = None,
    ) -> list[dict]:
        embedding = RAGService.embed(query)
        embedding_literal = "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"

        concept_filter = ""
        params: dict[str, object] = {"embedding": embedding_literal, "top_k": top_k}
        if concepts:
            concept_filter = "AND concepts && CAST(:concepts AS TEXT[])"
            params["concepts"] = concepts

        sql = text(
            f"""
            SELECT
                book_title,
                chapter,
                section,
                content,
                concepts,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM book_chunks
            WHERE 1=1 {concept_filter}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
            """
        )

        result = await db.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "source": f"{row.book_title} - {row.chapter or 'General'}",
                "section": row.section,
                "content": row.content,
                "concepts": row.concepts or [],
                "relevance_score": round(float(row.similarity), 3),
            }
            for row in rows
        ]
