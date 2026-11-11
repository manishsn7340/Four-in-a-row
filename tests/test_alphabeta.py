"""Regression tests for plain Alpha-Beta pruning."""

from __future__ import annotations

from agents.alphabeta import AlphaBetaAgent
from agents.minimax import MinimaxAgent
from game.board import Board
from helpers import play, seeded_positions, snapshot


def test_alphabeta_matches_minimax_on_seeded_positions_at_depths_one_to_four() -> None:
    """Keep plain Alpha-Beta exactly equivalent to Minimax before optimizations."""
    for depth in range(1, 5):
        for position in seeded_positions(50, 314159, 5, 16):
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
