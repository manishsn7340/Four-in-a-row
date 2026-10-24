"""Board evaluation heuristics for Four in a Row."""

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


def _playable_row(board: Board, col: int) -> int:
    """Return the landing row in col, or -1 if full."""
    for row in range(ROWS):
        if board.grid[row][col] == 0:
            return row
    return -1


def _all_windows(board: Board) -> list[list[tuple[int, int]]]:
    """Return all 69 4-cell windows across rows, cols, and diagonals."""
    windows: list[list[tuple[int, int]]] = []

    # Horizontal (24)
    for r in range(ROWS):
        for c in range(COLS - 3):
            windows.append([(r, c + k) for k in range(4)])

    # Vertical (21)
    for r in range(ROWS - 3):
        for c in range(COLS):
            windows.append([(r + k, c) for k in range(4)])

    # Diagonal down-right (12)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            windows.append([(r + k, c + k) for k in range(4)])

    # Diagonal up-right (12)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            windows.append([(r - k, c + k) for k in range(4)])

    return windows


def _count_double_threats(board: Board, player: int, playable: dict[int, int]) -> int:
    """Return 1 if player has two or more distinct playable winning cells, else 0."""
    winning_cols: set[int] = set()

    for window in _all_windows(board):
        cells = [(r, c) for r, c in window]
        mine = sum(board.grid[r][c] == player for r, c in cells)
        empty_cells = [(r, c) for r, c in cells if board.grid[r][c] == 0]
        if mine == 3 and len(empty_cells) == 1:
            er, ec = empty_cells[0]
            if playable.get(ec) == er:
                winning_cols.add(ec)

    return 1 if len(winning_cols) >= 2 else 0


def _raw_score(
    board: Board, player: int, w: Mapping[str, int], playable: dict[int, int]
) -> int:
    """Compute one-sided score for player."""
    opponent = 3 - player
    score = 0

    # Center column bonus
    center_col = COLS // 2
    mine_center = sum(board.grid[r][center_col] == player for r in range(ROWS))
    score += w.get("center", 0) * mine_center

    if "two" not in w:
        return score

    for window in _all_windows(board):
        cells = [(r, c) for r, c in window]
        mine = sum(board.grid[r][c] == player for r, c in cells)
        theirs = sum(board.grid[r][c] == opponent for r, c in cells)

        if mine > 0 and theirs > 0:
            continue

        empty_cells = [(r, c) for r, c in cells if board.grid[r][c] == 0]
        n_empty = len(empty_cells)

        if theirs == 0:
            if mine == 2 and n_empty == 2:
                score += w.get("two", 0)
            elif mine == 3 and n_empty == 1:
                score += w.get("three", 0)
                er, ec = empty_cells[0]
                if playable.get(ec) == er:
                    score += w.get("playable_three", 0)

    score += w.get("double_threat", 0) * _count_double_threats(board, player, playable)
    return score


def evaluate(
    board: Board, player: int, weights: Mapping[str, int] | None = None
) -> int:
    """Score board from player's perspective antisymmetrically."""
    if player not in (1, 2):
        raise ValueError("Player must be 1 or 2.")

    opponent = 3 - player

    winner = board.winner()
    if winner == player:
        return WIN_SCORE
    if winner != 0:
        return -WIN_SCORE
    if board.is_full():
        return 0

    w: Mapping[str, int] = BASIC_WEIGHTS if weights is None else weights

    playable: dict[int, int] = {}
    for col in range(COLS):
        row = _playable_row(board, col)
        if row >= 0:
            playable[col] = row

    return _raw_score(board, player, w, playable) - _raw_score(board, opponent, w, playable)
