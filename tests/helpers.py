"""Small helpers shared by several test files."""

from __future__ import annotations

import random

from game.board import Board


def play(columns: list[int]) -> Board:
    """Play a legal sequence of columns and return the resulting board."""
    board = Board()
    for col in columns:
        board.drop(col)
    return board


def snapshot(board: Board) -> tuple:
    """Everything a search must restore: cells, move history and hash."""
    return tuple(tuple(row) for row in board.grid), tuple(board.move_history), board.hash


def seeded_positions(count: int, seed: int, min_moves: int, max_moves: int) -> list[Board]:
    """`count` reproducible, non-terminal positions reached by random play."""
    rng = random.Random(seed)
    positions: list[Board] = []
    while len(positions) < count:
        board = Board()
        for _ in range(rng.randint(min_moves, max_moves)):
            if board.is_terminal():
                break
            board.drop(rng.choice(board.legal_moves()))
        if not board.is_terminal():
            positions.append(board)
    return positions
