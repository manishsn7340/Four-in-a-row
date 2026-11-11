"""Unit tests for the hint analysis module."""

from __future__ import annotations

from config import WIN_SCORE
from game.board import Board
from helpers import snapshot
from gui.hint import analyze


def test_hint_empty_board_returns_scores_and_restores_board() -> None:
    board = Board()
    before = snapshot(board)
    scores, reason = analyze(board, depth=3)

    assert len(scores) == 7
    assert 3 in scores  # center column present
    assert isinstance(reason, str) and len(reason) > 0
    assert snapshot(board) == before


def test_hint_detects_immediate_win() -> None:
    board = Board()
    # P1: 0, P2: 0, P1: 1, P2: 1, P1: 2, P2: 2 -> P1 can win at col 3
    for c in [0, 0, 1, 1, 2, 2]:
        board.drop(c)

    before = snapshot(board)
    scores, reason = analyze(board, depth=3)

    assert scores[3] >= WIN_SCORE
    assert max(scores, key=lambda c: scores[c]) == 3
    assert "Wins immediately" in reason
    assert snapshot(board) == before


def test_hint_detects_opponent_threat_and_blocks() -> None:
    board = Board()
    # P1: 5, P2: 0, P1: 5, P2: 1, P1: 6, P2: 2 -> P2 threatens win at col 3. P1 must block col 3!
    for c in [5, 0, 5, 1, 6, 2]:
        board.drop(c)

    before = snapshot(board)
    scores, reason = analyze(board, depth=3)

    best_col = max(scores, key=lambda c: scores[c])
    assert best_col == 3
    assert "Blocks" in reason
    assert snapshot(board) == before


def test_hint_on_terminal_board() -> None:
    board = Board()
    for c in [0, 1, 0, 1, 0, 1, 0]:  # P1 wins on col 0
        board.drop(c)
    assert board.winner() == 1
    scores, reason = analyze(board, depth=3)
    assert scores == {}
    assert reason == ""
