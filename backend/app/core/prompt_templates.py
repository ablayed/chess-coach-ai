from typing import Any

import chess


COACHING_SYSTEM_PROMPT = """You are an expert chess coach. You explain positions to {level} players.

CRITICAL RULES:
- Every explanation must be SPECIFIC to THIS position. Never give generic advice.
- Reference the ACTUAL pieces, squares, and plans in this position.
- If the user's move is different from the engine's best, explain the CONCRETE difference in outcome.
- Use the book passages to support your explanation with chess principles.
- Vary your language; do not start every explanation the same way.
- NEVER hallucinate moves not present in the engine analysis.
- Keep explanations {length_guide}.
"""


COACHING_USER_PROMPT = """## Position
FEN: {fen}
{board_narrative}

## Moves
{last_move_line}
{user_move_line}
Engine's best move: {best_move}
Evaluation change: {eval_before} -> {eval_after} ({classification})

## Engine Lines
{pv_lines}

## Position Characteristics
Phase: {phase}
{opening_name_line}
Tactical motifs: {tactical_motifs}
Strategic themes: {strategic_themes}
King safety: {king_safety}

## Relevant Chess Literature
{book_passages}

## Task
{task_instruction}"""


GAME_SUMMARY_PROMPT = """You are summarizing a chess game for coaching purposes.

Player played as {color}.
Overall accuracy: {accuracy}%
Move breakdown: {move_breakdown}
Key mistakes were on moves: {critical_moves}

Common themes in errors: {error_themes}

Provide a 3-5 sentence coaching summary: what went well, what to improve, and one specific exercise or concept to study."""


def build_board_narrative(
    board: chess.Board,
    best_move_san: str | None,
    user_move_san: str | None = None,
    concepts: dict[str, Any] | None = None,
) -> str:
    """Generate a plain-English description of the current position."""
    parts: list[str] = []
    turn = "White" if board.turn == chess.WHITE else "Black"
    parts.append(f"{turn} to move.")

    white_material = sum(
        len(board.pieces(piece_type, chess.WHITE)) * value
        for piece_type, value in (
            (chess.PAWN, 1),
            (chess.KNIGHT, 3),
            (chess.BISHOP, 3),
            (chess.ROOK, 5),
            (chess.QUEEN, 9),
        )
    )
    black_material = sum(
        len(board.pieces(piece_type, chess.BLACK)) * value
        for piece_type, value in (
            (chess.PAWN, 1),
            (chess.KNIGHT, 3),
            (chess.BISHOP, 3),
            (chess.ROOK, 5),
            (chess.QUEEN, 9),
        )
    )
    diff = white_material - black_material
    if diff > 0:
        parts.append(f"White is up {diff} point{'s' if diff > 1 else ''} of material.")
    elif diff < 0:
        abs_diff = abs(diff)
        parts.append(f"Black is up {abs_diff} point{'s' if abs_diff > 1 else ''} of material.")
    else:
        parts.append("Material is equal.")

    castling: list[str] = []
    if board.has_kingside_castling_rights(chess.WHITE):
        castling.append("White can castle kingside")
    if board.has_queenside_castling_rights(chess.WHITE):
        castling.append("White can castle queenside")
    if board.has_kingside_castling_rights(chess.BLACK):
        castling.append("Black can castle kingside")
    if board.has_queenside_castling_rights(chess.BLACK):
        castling.append("Black can castle queenside")
    if castling:
        parts.append(f"Castling rights: {'; '.join(castling)}.")

    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is not None:
        wk_name = chess.square_name(wk)
        if chess.square_file(wk) in (5, 6) and chess.square_rank(wk) == 0:
            parts.append(f"White king is castled kingside (on {wk_name}).")
        elif chess.square_rank(wk) == 0 and chess.square_file(wk) == 4:
            parts.append(f"White king is still in the center (on {wk_name}).")
    if bk is not None:
        bk_name = chess.square_name(bk)
        if chess.square_file(bk) in (5, 6) and chess.square_rank(bk) == 7:
            parts.append(f"Black king is castled kingside (on {bk_name}).")
        elif chess.square_rank(bk) == 7 and chess.square_file(bk) == 4:
            parts.append(f"Black king is still in the center (on {bk_name}).")

    if best_move_san:
        try:
            move = board.parse_san(best_move_san)
            piece = board.piece_at(move.from_square)
            target = board.piece_at(move.to_square)
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)

            if board.is_castling(move):
                side = "kingside" if chess.square_file(move.to_square) > 4 else "queenside"
                parts.append(f"The engine recommends {side} castling ({best_move_san}).")
            elif target:
                piece_name = chess.piece_name(piece.piece_type) if piece else "piece"
                target_name = chess.piece_name(target.piece_type)
                parts.append(
                    f"The engine recommends capturing the {target_name} on {to_sq} with the {piece_name} ({best_move_san})."
                )
            elif piece:
                piece_name = chess.piece_name(piece.piece_type)
                parts.append(f"The engine recommends moving the {piece_name} from {from_sq} to {to_sq} ({best_move_san}).")
            else:
                parts.append(f"The engine recommends {best_move_san}.")
        except (ValueError, AttributeError):
            parts.append(f"The engine recommends {best_move_san}.")

    if user_move_san and user_move_san != best_move_san:
        try:
            move = board.parse_san(user_move_san)
            piece = board.piece_at(move.from_square)
            target = board.piece_at(move.to_square)
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)

            if piece:
                piece_name = chess.piece_name(piece.piece_type)
                if target:
                    target_name = chess.piece_name(target.piece_type)
                    parts.append(
                        f"Instead, you played {user_move_san}, capturing the {target_name} on {to_sq} with your {piece_name}."
                    )
                else:
                    parts.append(f"Instead, you played {user_move_san}, moving your {piece_name} from {from_sq} to {to_sq}.")
            else:
                parts.append(f"Instead, you played {user_move_san}.")
        except (ValueError, AttributeError):
            parts.append(f"Instead, you played {user_move_san}.")

    legal_moves_count = len(list(board.legal_moves))
    if legal_moves_count < 10:
        parts.append(f"This is a tense position with only {legal_moves_count} legal moves.")
    elif legal_moves_count > 35:
        parts.append(f"This is an open position with {legal_moves_count} legal moves available.")

    if concepts:
        tension = concepts.get("tension")
        if tension and tension != "moderate_tension":
            parts.append(f"Current tension profile: {str(tension).replace('_', ' ')}.")

        placements = concepts.get("piece_placement", [])
        if placements:
            readable = ", ".join(str(p).replace("_", " ") for p in placements[:3])
            parts.append(f"Notable piece placement: {readable}.")

    return " ".join(parts)


def _build_task_instruction(user_move: str | None, best_move: str, classification: str) -> str:
    """Generate an instruction adapted to the player's move quality."""
    if not user_move:
        return "Explain the key ideas in this position and why the engine's recommended move is strong."

    if classification in ("brilliant", "great"):
        return f"Praise the move {user_move} and explain why it is excellent. What does it achieve?"
    if classification == "good":
        return f"Briefly acknowledge {user_move} is reasonable, then explain what {best_move} achieves that {user_move} does not."
    if classification == "inaccuracy":
        return (
            f"Explain why {user_move} is slightly imprecise. What opportunity does {best_move} exploit that {user_move} misses? "
            "Be constructive."
        )
    if classification == "mistake":
        return (
            f"Explain clearly what is wrong with {user_move}. What concrete problem does it create? "
            f"Then explain why {best_move} is significantly better."
        )
    if classification == "blunder":
        return (
            f"Explain what {user_move} loses or allows. Be direct about the tactical or strategic consequence. "
            f"Then show how {best_move} avoids this."
        )
    return f"Compare {user_move} with the engine suggestion {best_move}."
