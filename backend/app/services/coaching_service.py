from typing import Any

import chess
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.concept_extractor import classify_move, extract_concepts
from app.core.prompt_templates import (
    COACHING_SYSTEM_PROMPT,
    COACHING_USER_PROMPT,
    _build_task_instruction,
    build_board_narrative,
)
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

llm_service = LLMService()


def _piece_at(board: chess.Board, square: chess.Square, piece_type: chess.PieceType, color: chess.Color) -> bool:
    piece = board.piece_at(square)
    return piece is not None and piece.piece_type == piece_type and piece.color == color


def _detect_opening_from_position(board: chess.Board) -> str | None:
    if _piece_at(board, chess.E4, chess.PAWN, chess.WHITE):
        if _piece_at(board, chess.E5, chess.PAWN, chess.BLACK):
            if _piece_at(board, chess.F3, chess.KNIGHT, chess.WHITE):
                if _piece_at(board, chess.C6, chess.KNIGHT, chess.BLACK):
                    if _piece_at(board, chess.B5, chess.BISHOP, chess.WHITE):
                        if _piece_at(board, chess.A6, chess.PAWN, chess.BLACK):
                            return "Ruy Lopez Morphy Defense"
                        return "Ruy Lopez Spanish Game"
                    if _piece_at(board, chess.C4, chess.BISHOP, chess.WHITE):
                        if _piece_at(board, chess.F6, chess.KNIGHT, chess.BLACK):
                            return "Two Knights Defense"
                        if _piece_at(board, chess.C5, chess.BISHOP, chess.BLACK):
                            return "Giuoco Piano Italian Game"
                        return "Italian Game Giuoco Piano"
                    if _piece_at(board, chess.D4, chess.PAWN, chess.WHITE):
                        return "Scotch Game"
                    return "Open Game King Pawn"
                if _piece_at(board, chess.F6, chess.KNIGHT, chess.BLACK):
                    return "Petrov Defense Russian Game"
            if _piece_at(board, chess.F4, chess.PAWN, chess.WHITE):
                return "King's Gambit"
            return "Open Game King Pawn"
        if _piece_at(board, chess.C5, chess.PAWN, chess.BLACK):
            return "Sicilian Defense"
        if _piece_at(board, chess.C6, chess.PAWN, chess.BLACK):
            return "Caro-Kann Defense"
        if _piece_at(board, chess.E6, chess.PAWN, chess.BLACK):
            return "French Defense"
        if _piece_at(board, chess.D5, chess.PAWN, chess.BLACK):
            return "Scandinavian Defense"
        if _piece_at(board, chess.D6, chess.PAWN, chess.BLACK):
            if _piece_at(board, chess.D4, chess.PAWN, chess.WHITE) and _piece_at(board, chess.G6, chess.PAWN, chess.BLACK):
                return "Pirc Defense"
            return "King Pawn Opening"
        return "King Pawn Opening"

    if _piece_at(board, chess.D4, chess.PAWN, chess.WHITE):
        if _piece_at(board, chess.D5, chess.PAWN, chess.BLACK):
            if _piece_at(board, chess.C4, chess.PAWN, chess.WHITE):
                if _piece_at(board, chess.E6, chess.PAWN, chess.BLACK):
                    return "Queen's Gambit Declined"
                if _piece_at(board, chess.C4, chess.PAWN, chess.BLACK):
                    return "Queen's Gambit Accepted"
                return "Queen's Gambit"
            return "Closed Game Queen Pawn"
        if _piece_at(board, chess.F6, chess.KNIGHT, chess.BLACK):
            if _piece_at(board, chess.C4, chess.PAWN, chess.WHITE) and _piece_at(board, chess.G6, chess.PAWN, chess.BLACK):
                return "King's Indian Defense"
            if _piece_at(board, chess.C4, chess.PAWN, chess.WHITE) and _piece_at(board, chess.E6, chess.PAWN, chess.BLACK):
                if _piece_at(board, chess.C3, chess.KNIGHT, chess.WHITE) and _piece_at(board, chess.B4, chess.BISHOP, chess.BLACK):
                    return "Nimzo-Indian Defense"
                if _piece_at(board, chess.F3, chess.KNIGHT, chess.WHITE) and _piece_at(board, chess.B6, chess.PAWN, chess.BLACK):
                    return "Queen's Indian Defense"
            if _piece_at(board, chess.C4, chess.PAWN, chess.WHITE) and _piece_at(board, chess.C5, chess.PAWN, chess.BLACK):
                return "Benoni Defense"
        return "Queen Pawn Opening"

    if _piece_at(board, chess.C4, chess.PAWN, chess.WHITE):
        return "English Opening"
    if _piece_at(board, chess.F3, chess.KNIGHT, chess.WHITE):
        return "Reti Opening"

    return None


def detect_opening_name(board: chess.Board) -> str | None:
    """Detect common opening names from move sequence, then board pattern fallback."""
    move_stack = list(board.move_stack)
    if move_stack:
        temp_board = chess.Board()
        san_moves: list[str] = []
        for move in move_stack[:10]:
            try:
                san_moves.append(temp_board.san(move))
                temp_board.push(move)
            except Exception:  # noqa: BLE001
                break

        move_str = " ".join(san_moves).lower()
        openings = {
            "e4 e5 nf3 nc6 bb5 a6": "Ruy Lopez Morphy Defense",
            "e4 e5 nf3 nc6 bb5": "Ruy Lopez Spanish Game",
            "e4 e5 nf3 nc6 bc4 nf6": "Two Knights Defense",
            "e4 e5 nf3 nc6 bc4 bc5": "Giuoco Piano Italian Game",
            "e4 e5 nf3 nc6 bc4": "Italian Game Giuoco Piano",
            "e4 e5 nf3 nc6 d4": "Scotch Game",
            "e4 e5 nf3 nf6": "Petrov Defense Russian Game",
            "e4 c5": "Sicilian Defense",
            "e4 c6": "Caro-Kann Defense",
            "e4 e6": "French Defense",
            "e4 d5": "Scandinavian Defense",
            "e4 e5 f4": "King's Gambit",
            "d4 d5 c4 e6": "Queen's Gambit Declined",
            "d4 d5 c4 dxc4": "Queen's Gambit Accepted",
            "d4 d5 c4": "Queen's Gambit",
            "d4 nf6 c4 g6": "King's Indian Defense",
            "d4 nf6 c4 e6 nc3 bb4": "Nimzo-Indian Defense",
            "d4 nf6 c4 e6 nf3 b6": "Queen's Indian Defense",
            "d4 nf6 c4 c5": "Benoni Defense",
            "e4 d6 d4 nf6 nc3 g6": "Pirc Defense",
            "c4": "English Opening",
            "nf3": "Reti Opening",
        }
        for pattern in sorted(openings.keys(), key=len, reverse=True):
            if move_str.startswith(pattern):
                return openings[pattern]
        if move_str.startswith("e4 e5"):
            return "Open Game King Pawn"
        if move_str.startswith("d4 d5"):
            return "Closed Game Queen Pawn"
        if move_str.startswith("e4"):
            return "King Pawn Opening"
        if move_str.startswith("d4"):
            return "Queen Pawn Opening"

    return _detect_opening_from_position(board)


def build_rag_query(
    board: chess.Board,
    fen: str,
    concepts: dict[str, Any],
    best_move_san: str | None = None,
    user_move_san: str | None = None,
) -> str:
    """Build a diverse RAG query grounded in this specific board state."""
    _ = fen
    parts: list[str] = []

    parts.append(concepts.get("phase", "middlegame"))

    tension = concepts.get("tension")
    if tension:
        parts.append(str(tension))

    generic_placements = {"White_bishop_pair", "Black_bishop_pair"}
    placements = [placement for placement in concepts.get("piece_placement", []) if placement not in generic_placements]
    for placement in placements[:3]:
        parts.append(str(placement))

    if best_move_san:
        try:
            move = board.parse_san(best_move_san)
            piece = board.piece_at(move.from_square)
            target_piece = board.piece_at(move.to_square)

            if board.is_castling(move):
                parts.append("castling king safety rook activation")
            elif target_piece:
                piece_name = chess.piece_name(piece.piece_type) if piece else "piece"
                target_name = chess.piece_name(target_piece.piece_type)
                parts.append(f"{piece_name} captures {target_name}")
                parts.append("exchange tactical calculation")
            elif piece and piece.piece_type == chess.PAWN:
                to_rank = chess.square_rank(move.to_square)
                if to_rank in (0, 7):
                    parts.append("pawn promotion endgame technique")
                elif to_rank in (3, 4):
                    parts.append("central pawn advance space advantage")
                else:
                    parts.append("pawn move pawn structure")
            elif piece and piece.piece_type == chess.KNIGHT:
                parts.append("knight maneuver outpost centralization")
            elif piece and piece.piece_type == chess.BISHOP:
                parts.append("bishop development diagonal control")
            elif piece and piece.piece_type == chess.ROOK:
                parts.append("rook open file seventh rank activity")
            elif piece and piece.piece_type == chess.QUEEN:
                parts.append("queen activity coordination")
            elif piece and piece.piece_type == chess.KING:
                parts.append("king activity endgame centralization")
        except (ValueError, AttributeError):
            pass

    if user_move_san and best_move_san and user_move_san != best_move_san:
        parts.append(f"why {best_move_san} is better than {user_move_san}")

    for motif in concepts.get("tactical_motifs", []):
        if motif not in ("capture_available",):
            parts.append(motif)

    generic_themes = {"center_control", "development_needed", "bishop_pair", "open_file"}
    specific_themes = [theme for theme in concepts.get("strategic_themes", []) if theme not in generic_themes]
    parts.extend(specific_themes[:2])

    if len(parts) <= 2:
        parts.extend(concepts.get("strategic_themes", [])[:2])

    if board.fullmove_number <= 15:
        opening_name = _detect_opening_with_candidate(board, best_move_san)
        if opening_name:
            parts.append(opening_name)

    deduped: list[str] = []
    seen: set[str] = set()
    for raw in parts:
        token = str(raw).strip()
        if token and token not in seen:
            deduped.append(token)
            seen.add(token)
    return " ".join(deduped)


def _format_eval_value(value: float | int | str) -> str:
    if isinstance(value, (int, float)):
        return f"{value / 100:+.1f}"
    return str(value)


def _detect_opening_with_candidate(board: chess.Board, best_move_san: str | None) -> str | None:
    opening_name = detect_opening_name(board)
    if opening_name:
        return opening_name

    if best_move_san:
        try:
            next_board = board.copy()
            next_board.push(next_board.parse_san(best_move_san))
            return detect_opening_name(next_board)
        except (ValueError, AttributeError):
            return None

    return None


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

        rag_query = build_rag_query(
            board=board,
            fen=fen,
            concepts=concepts,
            best_move_san=best_move,
            user_move_san=user_move,
        )

        book_passages = await RAGService.retrieve(
            db,
            rag_query,
            top_k=3,
            concepts=concepts.get("strategic_themes", [])[:2] or None,
        )

        pv_text_lines: list[str] = []
        for index, line in enumerate(pv_lines[:3], 1):
            eval_payload = line.get("evaluation", {}) if isinstance(line, dict) else {}
            eval_type = eval_payload.get("type", "cp")
            eval_value = eval_payload.get("value", 0)
            eval_str = f"{'M' if eval_type == 'mate' else ''}{eval_value}"
            pv_san = line.get("pv_san", []) if isinstance(line, dict) else []
            pv_seq = " ".join(pv_san[:8]) if pv_san else ""
            san = line.get("san", best_move) if isinstance(line, dict) else best_move
            pv_text_lines.append(f"  Line {index}: {san} (eval: {eval_str}) {pv_seq}".strip())
        pv_text = "\n".join(pv_text_lines) if pv_text_lines else "  (No principal variation available)"

        book_text_lines: list[str] = []
        for reference in book_passages:
            preview = reference["content"][:300].replace("\n", " ").strip()
            book_text_lines.append(f"  [{reference['source']}]: \"{preview}...\"")
        book_text = "\n".join(book_text_lines) if book_text_lines else "  (No directly relevant passages found)"

        opening_name = _detect_opening_with_candidate(board, best_move) if board.fullmove_number <= 15 else None
        board_narrative = build_board_narrative(
            board=board,
            best_move_san=best_move,
            user_move_san=user_move,
            concepts=concepts,
        )

        length_guide = {
            "beginner": "4-6 sentences, simple language",
            "intermediate": "5-8 sentences, use chess terminology",
            "advanced": "3-5 precise sentences focused on critical variations",
        }.get(player_level, "5-8 sentences, use chess terminology")

        system_prompt = COACHING_SYSTEM_PROMPT.format(
            level=player_level,
            length_guide=length_guide,
        )
        user_prompt = COACHING_USER_PROMPT.format(
            fen=fen,
            board_narrative=board_narrative,
            last_move_line=f"Last move played: {last_move}" if last_move else "Game start.",
            user_move_line=f"Your move: {user_move}" if user_move else "",
            best_move=best_move,
            eval_before=_format_eval_value(eval_before),
            eval_after=_format_eval_value(eval_after),
            classification=classification,
            pv_lines=pv_text,
            phase=concepts.get("phase", "unknown"),
            opening_name_line=f"Opening: {opening_name}" if opening_name else "",
            tactical_motifs=", ".join(concepts.get("tactical_motifs", [])) or "none detected",
            strategic_themes=", ".join(concepts.get("strategic_themes", [])) or "none detected",
            king_safety=concepts.get("king_safety", "unknown"),
            book_passages=book_text,
            task_instruction=_build_task_instruction(user_move, best_move, classification),
        )

        explanation = await llm_service.generate(system_prompt, user_prompt, max_tokens=800)

        key_concepts: list[str] = []
        key_concepts.extend(concepts.get("strategic_themes", []))
        key_concepts.extend(concepts.get("tactical_motifs", []))
        tension = concepts.get("tension")
        if tension:
            key_concepts.append(str(tension))
        key_concepts.extend(concepts.get("piece_placement", [])[:3])
        key_concepts = list(dict.fromkeys(key_concepts))

        return {
            "explanation": explanation,
            "book_references": [
                {
                    "source": reference["source"],
                    "passage_summary": reference["content"][:150] + "...",
                    "relevance_score": reference["relevance_score"],
                }
                for reference in book_passages
            ],
            "key_concepts": key_concepts,
            "move_classification": classification,
            "cp_loss": cp_loss,
        }
