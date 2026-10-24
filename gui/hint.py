"""Hint analysis: per-column scores and rule-based reason text."""

from __future__ import annotations

from config import COLS, ROWS, WIN_SCORE
from agents.evaluation import WEIGHTS, evaluate
from game.board import Board


def analyze(board: Board, depth: int = 3) -> tuple[dict[int, int], str]:
    """Return ({col: score}, reason) from the current player's perspective.

    Scores are computed with a depth-3 alpha-beta (full window per move).
    Positive = good for the current player.
    """
    if board.is_terminal():
        return {}, ""

    player = board.current_player()
    opp    = 3 - player
    scores: dict[int, int] = {}

    for col in board.legal_moves():
        board.drop(col)
        w = board.winner()
        if w == player:
            scores[col] = WIN_SCORE
        elif w != 0 or board.is_full():
            scores[col] = 0 if board.is_full() else -WIN_SCORE
        else:
            scores[col] = _ab(board, depth - 1, -WIN_SCORE, WIN_SCORE, False, player)
        board.undo()

    if not scores:
        return {}, ""

    best_col   = max(scores, key=lambda c: scores[c])
    best_score = scores[best_col]
    reason     = _reason(board, scores, best_col, best_score, player, opp)
    return scores, reason


# ── Internal alpha-beta (no TT, no stats — only for hint depth) ───────────────

def _ab(board: Board, depth: int, alpha: int, beta: int, maxi: bool, root: int) -> int:
    w = board.winner()
    if w == root:        return  WIN_SCORE
    if w != 0:           return -WIN_SCORE
    if board.is_full():  return 0
    if depth == 0:       return evaluate(board, root, WEIGHTS)

    if maxi:
        best = -WIN_SCORE
        for col in board.legal_moves():
            board.drop(col)
            try:
                best  = max(best, _ab(board, depth - 1, alpha, beta, False, root))
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
            finally:
                board.undo()
        return best
    else:
        best = WIN_SCORE
        for col in board.legal_moves():
            board.drop(col)
            try:
                best = min(best, _ab(board, depth - 1, alpha, beta, True, root))
                beta = min(beta, best)
                if alpha >= beta:
                    break
            finally:
                board.undo()
        return best


# ── Helpers ───────────────────────────────────────────────────────────────────

def _landing_row(board: Board, col: int) -> int:
    for row in range(ROWS):
        if board.grid[row][col] == 0:
            return row
    return -1


def _four_at(board: Board, row: int, col: int, player: int) -> bool:
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        n = 1
        for s in (1, -1):
            r, c = row + s * dr, col + s * dc
            while 0 <= r < ROWS and 0 <= c < COLS and board.grid[r][c] == player:
                n += 1; r += s * dr; c += s * dc
        if n >= 4:
            return True
    return False


def _would_win(board: Board, col: int, player: int) -> bool:
    """True if player can win by dropping in col right now."""
    row = _landing_row(board, col)
    if row < 0:
        return False
    board.grid[row][col] = player
    wins = _four_at(board, row, col, player)
    board.grid[row][col] = 0
    return wins


def _reason(
    board: Board,
    scores: dict[int, int],
    best: int,
    best_score: int,
    player: int,
    opp: int,
) -> str:
    """Return a one-line reason for the best column, in priority order."""
    if best_score >= WIN_SCORE:
        return f"Wins immediately — column {best} completes four in a row."
    if _would_win(board, best, opp):
        return f"Blocks the opponent's winning move at column {best}."
    if best_score > 50:
        return f"Creates a strong threat — column {best} is the sharpest move."
    if best == 3:
        return "Takes the center column — the strongest opening square."
    return f"Best positional play — column {best} builds toward four."
