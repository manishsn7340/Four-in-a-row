"""Tests for Alpha-Beta move ordering and iterative deepening."""

from __future__ import annotations

from time import perf_counter

from agents.alphabeta import AlphaBetaAgent
from game.board import Board
from helpers import seeded_positions


def test_move_ordering_preserves_scores_and_reduces_average_nodes() -> None:
    """Keep the same root scores while center-first order lowers total work."""
    plain_nodes = 0
    ordered_nodes = 0
    for position in seeded_positions(30, 271828, 6, 18):
        plain = AlphaBetaAgent(depth=5, use_ordering=False)
        ordered = AlphaBetaAgent(depth=5, use_ordering=True)

        plain.choose_move(position)
        ordered.choose_move(position)

        assert ordered.last_stats.score == plain.last_stats.score
        plain_nodes += plain.last_stats.nodes
        ordered_nodes += ordered.last_stats.nodes

    assert ordered_nodes < plain_nodes


def test_iterative_deepening_returns_a_legal_move_within_the_time_limit() -> None:
    """Keep a safe legal answer after a 0.2-second iterative search budget."""
    board = Board()
    agent = AlphaBetaAgent(
        depth=12,
        use_ordering=True,
        use_iterative_deepening=True,
        time_limit=0.2,
    )

    start = perf_counter()
    move = agent.choose_move(board)
    elapsed = perf_counter() - start

    assert move in board.legal_moves()
    assert elapsed <= 0.3
    assert agent.last_stats.time_s <= 0.3


def test_more_time_completes_more_iterative_depths() -> None:
    """Use a larger search budget to finish strictly more full depths."""
    short_budget = AlphaBetaAgent(
        depth=12,
        use_ordering=True,
        use_iterative_deepening=True,
        time_limit=0.01,
    )
    long_budget = AlphaBetaAgent(
        depth=12,
        use_ordering=True,
        use_iterative_deepening=True,
        time_limit=0.2,
    )

    assert short_budget.choose_move(Board()) in range(Board.COLS)
    assert long_budget.choose_move(Board()) in range(Board.COLS)
    assert long_budget.last_stats.depth_reached > short_budget.last_stats.depth_reached


def test_iterative_deepening_reports_once_per_completed_depth() -> None:
    """Send the GUI one progress update for every fully searched depth."""
    updates: list[dict] = []
    agent = AlphaBetaAgent(
        depth=4,
        use_ordering=True,
        use_iterative_deepening=True,
    )
    agent.on_progress = updates.append

    move = agent.choose_move(Board())

    assert move in range(Board.COLS)
    assert [update["depth"] for update in updates] == [1, 2, 3, 4]
    assert all("best_move" in update and "score" in update for update in updates)
