"""Heuristic board evaluation: centre control plus open twos, threes and double threats."""

from __future__ import annotations

from collections.abc import Mapping

from config import COLS, ROWS, WIN_SCORE
from game.board import Board

BASIC_WEIGHTS: dict[str, int] = {"center": 3}

WEIGHTS: dict[str, int] = {
    "center": 3,
    "two": 2,
    "three": 5,
    "opp_two": 2,
    "opp_three": 6,
    "playable_three": 8,
    "double_threat": 40,
}


def _make_windows() -> list[list[tuple[int, int]]]:
    """All 69 lines of four cells: horizontal, vertical and both diagonals."""
    windows = []
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (-1, 1)):
                cells = [(r + k * dr, c + k * dc) for k in range(4)]
                if all(0 <= rr < ROWS and 0 <= cc < COLS for rr, cc in cells):
                    windows.append(cells)
    return windows


WINDOWS = _make_windows()


def _side_score(board: Board, player: int, w: Mapping[str, int], landing: dict[int, int]) -> int:
    """Score the position for one player only."""
    grid = board.grid
    score = w.get("center", 0) * sum(grid[r][COLS // 2] == player for r in range(ROWS))
    if "two" not in w:  # basic weights: centre only
        return score

    threat_cols = set()  # columns where `player` could complete four right now
    for cells in WINDOWS:
        values = [grid[r][c] for r, c in cells]
        mine, empty = values.count(player), values.count(0)
        if mine + empty < 4:  # opponent disc blocks this window
            continue
        if mine == 2:
            score += w.get("two", 0)
        elif mine == 3:
            score += w.get("three", 0)
            r, c = cells[values.index(0)]
            if landing.get(c) == r:
                score += w.get("playable_three", 0)
                threat_cols.add(c)
    if len(threat_cols) >= 2:
        score += w.get("double_threat", 0)
    return score


def evaluate(board: Board, player: int, weights: Mapping[str, int] | None = None) -> int:
    """Score from `player`'s point of view; evaluate(b, 1) == -evaluate(b, 2)."""
    winner = board.winner()
    if winner:
        return WIN_SCORE if winner == player else -WIN_SCORE
    if board.is_full():
        return 0
    w = BASIC_WEIGHTS if weights is None else weights
    landing = {c: board.height(c) for c in board.legal_moves()}
    return _side_score(board, player, w, landing) - _side_score(board, 3 - player, w, landing)
