"""Tests for baseline agents, basic evaluation, and fixed-depth Minimax."""

from __future__ import annotations

from agents.base import SearchStats
from agents.evaluation import evaluate
from agents.minimax import MinimaxAgent
from agents.simple import GreedyAgent, RandomAgent
from config import GLOBAL_SEED, WIN_SCORE
from game.board import Board
from helpers import play, snapshot


def test_search_stats_start_with_empty_measurements() -> None:
    """Expose predictable zero-valued statistics before an agent searches."""
    assert SearchStats() == SearchStats(nodes=0, cutoffs=0, tt_hits=0)


def test_random_agent_is_seeded_and_leaves_the_board_unchanged() -> None:
    """Same random seed produces the same legal choice without board mutation."""
    board = play([3, 2, 3])
    before = snapshot(board)

    first = RandomAgent(seed=17).choose_move(board)
    second = RandomAgent(seed=17).choose_move(board)

    assert first == second
    assert first in board.legal_moves()
    assert snapshot(board) == before


def test_greedy_agent_wins_blocks_and_prefers_the_center() -> None:
    """Use the documented tactical priorities for the simple baseline agent."""
    winning_board = play([0, 0, 1, 1, 2, 2])
    blocking_board = play([6, 0, 6, 1, 5, 2])
    empty_board = Board()
    boards = (winning_board, blocking_board, empty_board)
    before = [snapshot(board) for board in boards]

    assert GreedyAgent().choose_move(winning_board) == 3
    assert GreedyAgent().choose_move(blocking_board) == 3
    assert GreedyAgent().choose_move(empty_board) == 3
    assert [snapshot(board) for board in boards] == before


def test_basic_evaluation_scores_center_and_terminal_positions() -> None:
    """Give the root player a small center bonus and clear terminal scores."""
    center_board = Board()
    center_board.drop(3)
    assert evaluate(center_board, 1) == 3
    assert evaluate(center_board, 2) == -3

    winning_board = play([0, 0, 1, 1, 2, 2, 3])
    assert evaluate(winning_board, 1) == WIN_SCORE
    assert evaluate(winning_board, 2) == -WIN_SCORE


def test_minimax_takes_an_immediate_win_and_records_search_stats() -> None:
    """Prefer a winning move and report meaningful measurements for the search."""
    board = play([0, 0, 1, 1, 2, 2])
    agent = MinimaxAgent(depth=3)

    assert agent.choose_move(board) == 3
    assert agent.last_stats.best_move == 3
    assert agent.last_stats.score == WIN_SCORE + 2
    assert agent.last_stats.nodes > 0
    assert agent.last_stats.time_s >= 0.0
    assert agent.last_stats.depth_reached == 3


def test_minimax_blocks_an_opponents_immediate_win() -> None:
    """Search one opponent reply deep enough to block a forced loss."""
    board = play([6, 0, 6, 1, 5, 2])

    assert MinimaxAgent(depth=2).choose_move(board) == 3


def test_minimax_sees_a_forced_win_in_three_plies() -> None:
    """Recognize a fork where the opponent can block only one winning column."""
    board = play([3, 6, 0, 3, 4, 6])
    agent = MinimaxAgent(depth=3)

    assert agent.choose_move(board) == 2
    assert agent.last_stats.score is not None
    assert agent.last_stats.score >= WIN_SCORE

    fork = board.copy()
    fork.drop(2)
    assert fork.winner() == 0
    for opponent_move in fork.legal_moves():
        reply = fork.copy()
        reply.drop(opponent_move)
        assert any(
            _wins_immediately(reply, move) for move in reply.legal_moves()
        )


def test_minimax_leaves_the_board_exactly_as_it_found_it() -> None:
    """Use drop and undo so a caller can safely reuse its board after searching."""
    board = play([3, 2, 4, 2, 5, 1])
    before = snapshot(board)

    move = MinimaxAgent(depth=3).choose_move(board)

    assert move in board.legal_moves()
    assert snapshot(board) == before


def test_minimax_beats_random_agent_in_seeded_depth_three_games() -> None:
    """Verify the Minimax baseline wins at least 18 of 20 reproducible games."""
    minimax_wins = 0
    for seed in range(GLOBAL_SEED, GLOBAL_SEED + 20):
        board = Board()
        minimax = MinimaxAgent(depth=3)
        random_agent = RandomAgent(seed=seed)
        while not board.is_terminal():
            agent = minimax if board.current_player() == 1 else random_agent
            board.drop(agent.choose_move(board))
        minimax_wins += board.winner() == 1

    assert minimax_wins >= 18


def _wins_immediately(board: Board, col: int) -> bool:
    """Return whether the current player wins by dropping in ``col``."""
    probe = board.copy()
    player = probe.current_player()
    probe.drop(col)
    return probe.winner() == player
