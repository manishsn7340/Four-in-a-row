"""Hint: score every column with a shallow Alpha-Beta search and explain the best one."""

from __future__ import annotations

from agents.evaluation import WEIGHTS, evaluate
from config import WIN_SCORE
from game.board import Board


def analyze(board: Board, depth: int = 3) -> tuple[dict[int, int], str]:
    """Return ({column: score}, reason) for the player to move. Higher is better."""
    if board.is_terminal():
        return {}, ""
    me = board.current_player()
    scores = {}
    for col in board.legal_moves():
        board.drop(col)
        scores[col] = _search(board, depth - 1, -WIN_SCORE, WIN_SCORE, False, me)
        board.undo()
    best = max(scores, key=scores.get)
    return scores, _reason(board, best, scores[best], me)


def _search(board: Board, depth: int, alpha: int, beta: int, maximizing: bool, me: int) -> int:
    """Alpha-Beta without extras; wins and losses are clamped to +/-WIN_SCORE."""
    winner = board.winner()
    if winner:
        return WIN_SCORE if winner == me else -WIN_SCORE
    if board.is_full():
        return 0
    if depth == 0:
        return evaluate(board, me, WEIGHTS)
    best = -WIN_SCORE if maximizing else WIN_SCORE
    for col in board.legal_moves():
        board.drop(col)
        value = _search(board, depth - 1, alpha, beta, not maximizing, me)
        board.undo()
        if maximizing:
            best = max(best, value)
            alpha = max(alpha, best)
        else:
            best = min(best, value)
            beta = min(beta, best)
        if alpha >= beta:
            break
    return best


def _reason(board: Board, best: int, score: int, me: int) -> str:
    """One plain-language sentence, checked in priority order."""
    if score >= WIN_SCORE:
        return f"Wins immediately — column {best + 1} completes four in a row."
    if board.would_win(best, 3 - me):
        return f"Blocks the opponent's winning move at column {best + 1}."
    if score > 50:
        return f"Creates a strong threat — column {best + 1} is the sharpest move."
    if best == 3:
        return "Takes the center column — the strongest opening square."
    return f"Best positional play — column {best + 1} builds toward four."
