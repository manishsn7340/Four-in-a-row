"""Regression tests for plain Alpha-Beta pruning."""

from __future__ import annotations

import random

from agents.alphabeta import AlphaBetaAgent
from agents.minimax import MinimaxAgent
from game.board import Board


def play(columns: list[int]) -> Board:
    """Play a legal sequence of columns and return the resulting board."""
    board = Board()
    for col in columns:
        board.drop(col)
    return board


def seeded_positions(count: int) -> list[Board]:
    """Create non-terminal, reproducible positions for search comparisons."""
    rng = random.Random(314159)
    positions: list[Board] = []
    while len(positions) < count:
        board = Board()
        for _ in range(rng.randint(5, 16)):
            if board.is_terminal():
                break
            board.drop(rng.choice(board.legal_moves()))
        if not board.is_terminal():
            positions.append(board)
    return positions


def snapshot(board: Board) -> tuple[tuple[tuple[int, ...], ...], tuple[int, ...]]:
    """Capture board cells and history to prove a search restored both."""
    return tuple(tuple(row) for row in board.grid), tuple(board.move_history)


def test_alphabeta_matches_minimax_on_seeded_positions_at_depths_one_to_four() -> None:
    """Keep plain Alpha-Beta exactly equivalent to Minimax before optimizations."""
    for depth in range(1, 5):
        for position in seeded_positions(50):
            before = snapshot(position)
            minimax = MinimaxAgent(depth=depth)
            alphabeta = AlphaBetaAgent(depth=depth, use_ordering=False)

            minimax_move = minimax.choose_move(position)
            alphabeta_move = alphabeta.choose_move(position)

            assert alphabeta_move == minimax_move
            assert alphabeta.last_stats.score == minimax.last_stats.score
            assert snapshot(position) == before


def test_alphabeta_prunes_nodes_on_a_position_deeper_than_four_plies() -> None:
    """Visit fewer nodes than Minimax and record at least one cutoff."""
    position = play([3, 6, 0, 3, 4, 6])
    assert len(position.move_history) > 4
    before = snapshot(position)
    minimax = MinimaxAgent(depth=5)
    alphabeta = AlphaBetaAgent(depth=5, use_ordering=False)

    minimax_move = minimax.choose_move(position)
    alphabeta_move = alphabeta.choose_move(position)

    assert alphabeta_move == minimax_move
    assert alphabeta.last_stats.score == minimax.last_stats.score
    assert alphabeta.last_stats.nodes < minimax.last_stats.nodes
    assert alphabeta.last_stats.cutoffs > 0
    assert snapshot(position) == before
