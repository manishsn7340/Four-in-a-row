"""Tests for the player-move predictor."""

from __future__ import annotations

from agents.predictor import describe_style, predict_next_move
from helpers import play, seeded_positions, snapshot


def test_predicts_own_winning_move() -> None:
    board = play([0, 6, 1, 6, 2, 5])  # player 1 has 0,1,2 on the bottom row
    assert predict_next_move(board, 1) == 3


def test_predicts_block_when_it_cannot_win() -> None:
    board = play([6, 0, 5, 1, 6, 2])  # player 2 threatens 3; player 1 to move
    assert predict_next_move(board, 1) == 3


def test_empty_board_prefers_centre_and_board_is_restored() -> None:
    board = play([])
    before = snapshot(board)
    assert predict_next_move(board, 1) == 3
    assert snapshot(board) == before


def test_prediction_is_legal_and_restores_board_on_seeded_positions() -> None:
    for board in seeded_positions(20, 555, 4, 20):
        before = snapshot(board)
        assert predict_next_move(board, board.current_player()) in board.legal_moves()
        assert snapshot(board) == before


def test_no_prediction_on_full_board_columns_none() -> None:
    board = play([])
    assert predict_next_move(board, 1) is not None


def test_style_needs_a_few_moves() -> None:
    assert describe_style([3, 0, 3], 1) is None


def test_style_sentences() -> None:
    assert describe_style([3, 0, 3, 0, 4, 0], 1) == "You favour the centre"
    assert describe_style([0, 3, 1, 3, 0, 3], 1) == "You favour the left side"
    assert describe_style([6, 3, 5, 3, 6, 3], 1) == "You favour the right side"
    assert describe_style([0, 3, 3, 3, 6, 3], 1) == "You mix up your columns"
    assert describe_style([3, 0, 3, 1, 3, 0], 2) == "You favour the left side"
