"""Simple deterministic baseline agents for Four in a Row."""

from __future__ import annotations

import random
from time import perf_counter

from agents.base import Agent, SearchStats
from config import GLOBAL_SEED, MOVE_ORDER, WIN_SCORE
from game.board import Board


class RandomAgent(Agent):
    """Choose legal moves using an isolated, seeded random generator."""

    def __init__(self, seed: int = GLOBAL_SEED, name: str | None = None) -> None:
        """Create a random baseline whose sequence is reproducible from ``seed``."""
        super().__init__(name or "Random")
        self._rng = random.Random(seed)

    def choose_move(self, board: Board) -> int:
        """Choose one legal column without changing ``board``."""
        start = perf_counter()
        legal_moves = board.legal_moves()
        if not legal_moves:
            raise ValueError("Cannot choose a move on a full board.")

        move = self._rng.choice(legal_moves)
        self.last_stats = SearchStats(
            time_s=perf_counter() - start,
            best_move=move,
        )
        return move


class GreedyAgent(Agent):
    """Take immediate wins, block immediate losses, then prefer the center."""

    def __init__(self, name: str | None = None) -> None:
        """Create the deterministic tactical baseline agent."""
        super().__init__(name or "Greedy")

    def choose_move(self, board: Board) -> int:
        """Choose a tactical or center-first legal move without changing ``board``."""
        start = perf_counter()
        legal_moves = board.legal_moves()
        if not legal_moves:
            raise ValueError("Cannot choose a move on a full board.")

        player = board.current_player()
        opponent = 2 if player == 1 else 1
        ordered_moves = _center_first_moves(legal_moves)
        for col in ordered_moves:
            if _is_winning_placement(board, col, player):
                return self._finish(start, col, WIN_SCORE)
        for col in ordered_moves:
            if _is_winning_placement(board, col, opponent):
                return self._finish(start, col, 0)
        return self._finish(start, ordered_moves[0], 0)

    def _finish(self, start: float, move: int, score: float) -> int:
        """Store the result of a completed greedy decision and return its move."""
        self.last_stats = SearchStats(
            time_s=perf_counter() - start,
            best_move=move,
            score=score,
        )
        return move


def _center_first_moves(legal_moves: list[int]) -> list[int]:
    """Order legal columns from the center outward using the project convention."""
    legal_set = set(legal_moves)
    return [col for col in MOVE_ORDER if col in legal_set]


def _is_winning_placement(board: Board, col: int, player: int) -> bool:
    """Test whether placing ``player`` in ``col`` would immediately make four."""
    row = next(row for row in range(board.ROWS) if board.grid[row][col] == 0)
    board.grid[row][col] = player
    try:
        return any(
            _line_length(board, row, col, row_step, col_step, player) >= 4
            for row_step, col_step in ((0, 1), (1, 0), (1, 1), (1, -1))
        )
    finally:
        board.grid[row][col] = 0


def _line_length(
    board: Board, row: int, col: int, row_step: int, col_step: int, player: int
) -> int:
    """Count one complete same-player line through a temporary placement."""
    length = 1
    for direction in (-1, 1):
        next_row = row + direction * row_step
        next_col = col + direction * col_step
        while 0 <= next_row < board.ROWS and 0 <= next_col < board.COLS:
            if board.grid[next_row][next_col] != player:
                break
            length += 1
            next_row += direction * row_step
            next_col += direction * col_step
    return length
