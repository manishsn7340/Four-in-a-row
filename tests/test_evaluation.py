"""Tests for evaluation heuristics."""

from __future__ import annotations

import random

import pytest

from agents.alphabeta import AlphaBetaAgent
from agents.evaluation import BASIC_WEIGHTS, WEIGHTS, evaluate
from game.board import Board


def _play_game(agent1: AlphaBetaAgent, agent2: AlphaBetaAgent, opening: list[int]) -> int:
    """Play one game with a forced opening and return winner."""
    board = Board()
    for col in opening:
        if board.is_terminal():
            break
        board.drop(col)
    while not board.is_terminal():
        agent = agent1 if board.current_player() == 1 else agent2
        board.drop(agent.choose_move(board))
    return board.winner()


def _varied_positions(n: int, seed: int = 1234) -> list[Board]:
    """Generate n non-terminal seeded positions."""
    rng = random.Random(seed)
    positions: list[Board] = []
    while len(positions) < n:
        board = Board()
        for _ in range(rng.randint(4, 20)):
            if board.is_terminal():
                break
            board.drop(rng.choice(board.legal_moves()))
        if not board.is_terminal():
            positions.append(board)
    return positions


class TestAntisymmetry:
    """Test evaluate(board, 1) == -evaluate(board, 2)."""

    @pytest.mark.parametrize("position", _varied_positions(50))
    def test_full_weights_antisymmetric(self, position: Board) -> None:
        assert evaluate(position, 1, WEIGHTS) == -evaluate(position, 2, WEIGHTS)

    @pytest.mark.parametrize("position", _varied_positions(50))
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
        for board in _varied_positions(30, seed=9999):
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

    def test_playable_three_bonus_via_drops(self) -> None:
        board = Board()
        for col in [0, 0, 1, 1, 2, 0]:
            board.drop(col)
        empty = Board()
        assert evaluate(board, 1, WEIGHTS) > evaluate(empty, 1, WEIGHTS)


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


_OPENINGS_SEED = 7777


def _generate_openings(n: int, length: int = 4, seed: int = _OPENINGS_SEED) -> list[list[int]]:
    rng = random.Random(seed)
    openings: list[list[int]] = []
    while len(openings) < n:
        board = Board()
        seq: list[int] = []
        for _ in range(length):
            legal = board.legal_moves()
            col = rng.choice(legal)
            board.drop(col)
            seq.append(col)
            if board.is_terminal():
                break
        if not board.is_terminal():
            openings.append(seq)
    return openings


class TestNewVsBasicMatch:
    """Benchmark full weights against basic weights in a 40-game match."""

    def test_match_result(self) -> None:
        openings = _generate_openings(20, length=4, seed=_OPENINGS_SEED)
        full_wins = 0
        basic_wins = 0
        draws = 0

        for opening in openings:
            # Game A: full as player 1
            full_agent = AlphaBetaAgent(
                depth=4, use_ordering=True, weights=WEIGHTS, name="Full"
            )
            basic_agent = AlphaBetaAgent(
                depth=4, use_ordering=True, weights=BASIC_WEIGHTS, name="Basic"
            )
            w = _play_game(full_agent, basic_agent, opening)
            if w == 1:
                full_wins += 1
            elif w == 2:
                basic_wins += 1
            else:
                draws += 1

            # Game B: full as player 2
            basic_first = AlphaBetaAgent(
                depth=4, use_ordering=True, weights=BASIC_WEIGHTS, name="Basic"
            )
            full_second = AlphaBetaAgent(
                depth=4, use_ordering=True, weights=WEIGHTS, name="Full"
            )
            w2 = _play_game(basic_first, full_second, opening)
            if w2 == 2:
                full_wins += 1
            elif w2 == 1:
                basic_wins += 1
            else:
                draws += 1

        print(f"\n40-game match: Full={full_wins} Basic={basic_wins} Draws={draws}")
        assert full_wins >= basic_wins
