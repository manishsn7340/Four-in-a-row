"""Predict what a player is likely to do next, and describe how they have been playing."""

from __future__ import annotations

from agents.evaluation import WEIGHTS, evaluate
from config import COLS
from game.board import Board


def predict_next_move(board: Board, player: int) -> int | None:
    """The column `player` is most likely to play: win if possible, else block the
    opponent's win, else the move that gives `player` the best evaluation.
    The board is restored before returning."""
    legal = board.legal_moves()
    if not legal:
        return None
    for target in (player, 3 - player):
        for col in legal:
            if board.would_win(col, target):
                return col
    best_col, best_score = legal[0], None
    for col in legal:
        board.drop(col)
        score = evaluate(board, player, WEIGHTS)
        board.undo()
        if best_score is None or score > best_score:
            best_col, best_score = col, score
    return best_col


def describe_style(moves: list[int], player: int, min_moves: int = 3) -> str | None:
    """A short sentence about which part of the board `player` favours, or None
    if they have played fewer than `min_moves` discs."""
    mine = moves[player - 1::2]
    if len(mine) < min_moves:
        return None
    centre = sum(2 <= c <= COLS - 3 for c in mine) / len(mine)
    left = sum(c < 2 for c in mine) / len(mine)
    right = sum(c > COLS - 3 for c in mine) / len(mine)
    if centre >= 0.6:
        return "You favour the centre"
    if left >= 0.4:
        return "You favour the left side"
    if right >= 0.4:
        return "You favour the right side"
    return "You mix up your columns"
