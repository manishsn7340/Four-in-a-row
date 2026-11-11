"""Tests for evaluation heuristics."""

from __future__ import annotations

import pytest

from agents.alphabeta import AlphaBetaAgent
from agents.evaluation import BASIC_WEIGHTS, WEIGHTS, evaluate
from experiments.arena import play_match
from game.board import Board
from helpers import seeded_positions


class TestAntisymmetry:
    """Test evaluate(board, 1) == -evaluate(board, 2)."""

    @pytest.mark.parametrize("position", seeded_positions(50, 1234, 4, 20))
    def test_full_weights_antisymmetric(self, position: Board) -> None:
        assert evaluate(position, 1, WEIGHTS) == -evaluate(position, 2, WEIGHTS)

    @pytest.mark.parametrize("position", seeded_positions(50, 1234, 4, 20))
    def test_basic_weights_antisymmetric(self, position: Board) -> None:
        assert evaluate(position, 1, None) == -evaluate(position, 2, None)


class TestBasicModeUnchanged:
    """Test backwards-compatibility of basic center-only weights."""

    def test_empty_board_basic(self) -> None:
        board = Board()
        assert evaluate(board, 1, None) == 0
        assert evaluate(board, 1, BASIC_WEIGHTS) == 0

    def test_center_disc_basic(self) -> None:
        board = Board()
        board.drop(3)
        board.drop(0)
        assert evaluate(board, 1, None) == 3
        assert evaluate(board, 1, BASIC_WEIGHTS) == 3

    def test_none_and_basic_weights_agree(self) -> None:
        for board in seeded_positions(30, 9999, 4, 20):
            assert evaluate(board, 1, None) == evaluate(board, 1, BASIC_WEIGHTS)


class TestOpenThreeHigher:
    """Test threat scoring against empty board."""

    def test_open_three_horizontal_via_drops(self) -> None:
        board = Board()
        for col in [0, 0, 1, 1, 2, 0]:
            board.drop(col)
        empty = Board()
        assert evaluate(board, 1, WEIGHTS) > evaluate(empty, 1, WEIGHTS)

    def test_open_three_vertical(self) -> None:
        board = Board()
        for _ in range(3):
            board.drop(3)
            board.drop(0)
        assert evaluate(board, 1, WEIGHTS) > 0


class TestHandMadePositions:
    """Test decisions and threats on specific board states."""

    def test_takes_immediate_win(self) -> None:
        board = Board()
        for p1c, p2c in [(0, 6), (1, 5), (2, 4)]:
            board.drop(p1c)
            board.drop(p2c)
        agent = AlphaBetaAgent(depth=2, use_ordering=False, weights=WEIGHTS)
        assert agent.choose_move(board) == 3

    def test_blocks_opponent_threat(self) -> None:
        board = Board()
        for p1c, p2c in [(6, 1), (5, 2), (0, 3)]:
            board.drop(p1c)
            board.drop(p2c)
        agent = AlphaBetaAgent(depth=3, use_ordering=False, weights=WEIGHTS)
        assert agent.choose_move(board) == 4

    def test_prefers_center(self) -> None:
        board = Board()
        agent = AlphaBetaAgent(depth=1, use_ordering=False, weights=WEIGHTS)
        assert agent.choose_move(board) == 3

    def test_double_threat_bonus_increases_score(self) -> None:
        single = Board()
        for p1c, p2c in [(0, 6), (1, 5), (2, 4)]:
            single.drop(p1c)
            single.drop(p2c)
        score_single = evaluate(single, 1, WEIGHTS)

        double = Board()
        for col in [3, 6, 3, 6, 3, 6, 0, 5, 1, 5, 2, 5]:
            double.drop(col)
        score_double = evaluate(double, 1, WEIGHTS)
        assert score_double >= score_single


class TestNewVsBasicMatch:
    """Benchmark full weights against basic weights in a 40-game match."""

    def test_match_result(self) -> None:
        # 20 random 4-move openings, each played once with either side moving first.
        full = AlphaBetaAgent(depth=4, use_ordering=True, weights=WEIGHTS, name="Full")
        basic = AlphaBetaAgent(depth=4, use_ordering=True, weights=BASIC_WEIGHTS, name="Basic")
        r = play_match(full, basic, n_games=40, seed=7777, openings=4)
        print(f"\n40-game match: Full={r.wins_a} Basic={r.wins_b} Draws={r.draws}")
        assert r.wins_a >= r.wins_b
