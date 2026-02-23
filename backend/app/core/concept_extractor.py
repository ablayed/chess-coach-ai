from typing import Any

import chess


def extract_concepts(board: chess.Board, eval_info: dict) -> dict[str, Any]:
    """Extract strategic and tactical concepts from a chess position."""
    _ = eval_info
    return {
        "phase": _detect_phase(board),
        "tactical_motifs": _detect_tactics(board),
        "strategic_themes": _detect_strategy(board),
        "king_safety": _assess_king_safety(board),
    }


def classify_move(cp_loss: float, is_sacrifice: bool = False) -> str:
    """Classify a move based on centipawn loss."""
    if cp_loss <= 0 and is_sacrifice:
        return "brilliant"
    if cp_loss <= 0:
        return "great"
    if cp_loss < 20:
        return "good"
    if cp_loss < 50:
        return "inaccuracy"
    if cp_loss < 150:
        return "mistake"
    return "blunder"


def _detect_phase(board: chess.Board) -> str:
    move_count = board.fullmove_number
    piece_count = len(board.piece_map()) - 2
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))

    if move_count <= 10 and piece_count >= 26:
        return "opening"
    if queens == 0 or piece_count <= 10:
        return "endgame"
    return "middlegame"


def _detect_tactics(board: chess.Board) -> list[str]:
    motifs: list[str] = []
    if board.is_check():
        motifs.append("check")

    for color in (chess.WHITE, chess.BLACK):
        king_sq = board.king(color)
        if king_sq is None:
            continue
        for attacker_sq in board.attackers(not color, king_sq):
            between = chess.SquareSet(chess.between(attacker_sq, king_sq))
            blockers = between & board.occupied_co[color]
            if len(blockers) == 1:
                motifs.append("pin")
                break

    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 100,
    }

    for square in board.piece_map():
        piece = board.piece_at(square)
        if piece is None:
            continue
        attacks = board.attacks(square)
        attacked_values: list[int] = []
        for target in attacks:
            target_piece = board.piece_at(target)
            if target_piece and target_piece.color != piece.color:
                attacked_values.append(piece_values.get(target_piece.piece_type, 0))

        high_value_attacks = [v for v in attacked_values if v > piece_values.get(piece.piece_type, 0)]
        if len(high_value_attacks) >= 2:
            motifs.append("fork")
            break

    for move in board.legal_moves:
        if board.is_capture(move):
            motifs.append("capture_available")
            break

    return sorted(set(motifs))


def _detect_strategy(board: chess.Board) -> list[str]:
    themes: list[str] = []

    center = (chess.E4, chess.D4, chess.E5, chess.D5)
    center_pawns = sum(
        1
        for square in center
        if (piece := board.piece_at(square)) is not None and piece.piece_type == chess.PAWN
    )
    if center_pawns >= 2:
        themes.append("center_control")

    for file_idx in range(8):
        has_white_pawn = any(
            board.piece_at(chess.square(file_idx, rank)) == chess.Piece(chess.PAWN, chess.WHITE)
            for rank in range(8)
        )
        has_black_pawn = any(
            board.piece_at(chess.square(file_idx, rank)) == chess.Piece(chess.PAWN, chess.BLACK)
            for rank in range(8)
        )
        if not has_white_pawn and not has_black_pawn:
            themes.append("open_file")
            break

    if board.fullmove_number <= 15:
        undeveloped = 0
        for square in (chess.B1, chess.C1, chess.F1, chess.G1):
            piece = board.piece_at(square)
            if piece and piece.color == chess.WHITE and piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                undeveloped += 1
        if undeveloped >= 2:
            themes.append("development_needed")

    for color in (chess.WHITE, chess.BLACK):
        for square in board.pieces(chess.PAWN, color):
            file_idx = chess.square_file(square)
            rank = chess.square_rank(square)
            is_passed = True
            direction = 1 if color == chess.WHITE else -1
            end = 8 if color == chess.WHITE else -1
            for check_rank in range(rank + direction, end, direction):
                for adj_file in (file_idx - 1, file_idx, file_idx + 1):
                    if 0 <= adj_file <= 7:
                        check_sq = chess.square(adj_file, check_rank)
                        target_piece = board.piece_at(check_sq)
                        if target_piece and target_piece.piece_type == chess.PAWN and target_piece.color != color:
                            is_passed = False
                            break
                if not is_passed:
                    break
            if is_passed:
                themes.append("passed_pawn")
                break

    for color in (chess.WHITE, chess.BLACK):
        bishops = board.pieces(chess.BISHOP, color)
        if len(bishops) >= 2:
            themes.append("bishop_pair")
            break

    return sorted(set(themes))


def _assess_king_safety(board: chess.Board) -> str:
    for color in (chess.WHITE, chess.BLACK):
        king_sq = board.king(color)
        if king_sq is None:
            continue
        king_zone = board.attacks(king_sq)
        attackers = sum(len(board.attackers(not color, square)) for square in king_zone)
        if attackers > 6:
            return "unsafe" if color == board.turn else "opponent_unsafe"
    return "safe"
