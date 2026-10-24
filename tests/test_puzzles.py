"""Unit tests for tactical puzzle trainer mode."""

from __future__ import annotations

from gui.puzzles import PUZZLES, get_puzzle


def test_puzzle_collection_integrity():
    assert len(PUZZLES) == 5
    for p in PUZZLES:
        assert p.id >= 1
        assert p.title
        assert p.difficulty in ("Easy", "Medium", "Hard")
        assert 0 <= p.solution_col < 7
        assert p.player_to_move in (1, 2)
        b = p.create_board()
        assert not b.is_terminal()
        assert b.current_player() == p.player_to_move


def test_puzzle_1_instant_win():
    p = get_puzzle(1)
    b = p.create_board()
    b.drop(p.solution_col)
    assert b.is_terminal()
    assert b.winner() == 1


def test_puzzle_2_emergency_block():
    p = get_puzzle(2)
    b = p.create_board()
    # If we drop in solution_col (col 2), it successfully blocks P2's vertical win
    b.drop(p.solution_col)
    assert not b.is_terminal()
    # Now if P2 plays col 2, it is row 4, not an instant win
    if 2 in b.legal_moves():
        b.drop(2)
        assert b.winner() != 2


def test_puzzle_3_double_threat_fork():
    p = get_puzzle(3)
    b = p.create_board()
    b.drop(p.solution_col)
    assert not b.is_terminal()
    # P1 now has cols 2, 3, 4 in row 0.
    # Whichever side P2 blocks (col 1 or col 5), P1 can play the other side to win!
    b_left = b.clone() if hasattr(b, "clone") else p.create_board()
    # Test left block
    b_test = p.create_board()
    b_test.drop(p.solution_col)
    b_test.drop(1)  # P2 blocks left
    b_test.drop(5)  # P1 plays right
    assert b_test.is_terminal()
    assert b_test.winner() == 1


def test_puzzle_4_diagonal_strike():
    p = get_puzzle(4)
    b = p.create_board()
    b.drop(p.solution_col)
    assert b.is_terminal()
    assert b.winner() == 1


def test_puzzle_5_inside_gap():
    p = get_puzzle(5)
    b = p.create_board()
    b.drop(p.solution_col)
    assert b.is_terminal()
    assert b.winner() == 1


def test_get_puzzle_clamping():
    assert get_puzzle(1).id == 1
    assert get_puzzle(5).id == 5
    assert get_puzzle(0).id == 1
    assert get_puzzle(99).id == 5
