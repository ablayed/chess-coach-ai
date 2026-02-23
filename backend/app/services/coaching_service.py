import chess
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.concept_extractor import classify_move, extract_concepts
from app.core.prompt_templates import COACHING_SYSTEM_PROMPT, COACHING_USER_PROMPT
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

llm_service = LLMService()


class CoachingService:
    @staticmethod
    async def explain_position(
        db: AsyncSession,
        fen: str,
        best_move: str,
        pv_lines: list[dict],
        user_move: str | None = None,
        last_move: str | None = None,
        eval_before: float = 0,
        eval_after: float = 0,
        player_level: str = "intermediate",
    ) -> dict:
        board = chess.Board(fen)
        concepts = extract_concepts(board, {})

        cp_loss = max(0.0, eval_before - eval_after) if user_move else 0.0
        classification = classify_move(cp_loss)

        rag_query_parts = [f"{concepts['phase']} position"]
        rag_query_parts.extend(concepts["strategic_themes"])
        rag_query_parts.extend(concepts["tactical_motifs"])
        rag_query = " ".join(rag_query_parts)

        book_passages = await RAGService.retrieve(
            db,
            rag_query,
            top_k=3,
            concepts=concepts["strategic_themes"][:2] or None,
        )

        pv_text = ""
        for i, line in enumerate(pv_lines[:3], 1):
            eval_type = line["evaluation"]["type"]
            eval_value = line["evaluation"]["value"]
            eval_str = f"{'M' if eval_type == 'mate' else ''}{eval_value}"
            pv_seq = " ".join(line.get("pv_san", [])[:6])
            pv_text += f"  Line {i}: {line['san']} (eval: {eval_str})  {pv_seq}\n"

        book_text = ""
        for ref in book_passages:
            preview = ref["content"][:300].replace("\n", " ").strip()
            book_text += f"  [{ref['source']}]: \"{preview}...\"\n"

        if not book_text.strip():
            book_text = "  (No directly relevant passages found)"

        system_prompt = COACHING_SYSTEM_PROMPT.format(level=player_level)
        user_prompt = COACHING_USER_PROMPT.format(
            fen=fen,
            last_move_line=f"Last move: {last_move}" if last_move else "",
            user_move_line=f"User played: {user_move}" if user_move else "",
            best_move=best_move,
            eval_before=eval_before,
            eval_after=eval_after,
            classification=classification,
            pv_lines=pv_text,
            phase=concepts["phase"],
            tactical_motifs=", ".join(concepts["tactical_motifs"]) or "none detected",
            strategic_themes=", ".join(concepts["strategic_themes"]) or "none detected",
            king_safety=concepts["king_safety"],
            book_passages=book_text,
            user_move_instruction=" and the user's move choice" if user_move else "",
        )

        explanation = await llm_service.generate(system_prompt, user_prompt, max_tokens=800)

        return {
            "explanation": explanation,
            "book_references": [
                {
                    "source": ref["source"],
                    "passage_summary": ref["content"][:150] + "...",
                    "relevance_score": ref["relevance_score"],
                }
                for ref in book_passages
            ],
            "key_concepts": concepts["strategic_themes"] + concepts["tactical_motifs"],
            "move_classification": classification,
            "cp_loss": cp_loss,
        }
