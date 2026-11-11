"""Tests for the Four in a Row board and rules layer."""

from __future__ import annotations

import random

import pytest

from game.board import Board
from helpers import play


def slow_winner(board: Board) -> int:
    """Find a winner with a full-board scan for comparison with Board.winner."""
    winners: set[int] = set()
    for row in range(Board.ROWS):
        for col in range(Board.COLS):
            player = board.grid[row][col]
            if player == 0:
                continue
            for row_step, col_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = [
                    (row + index * row_step, col + index * col_step)
                    for index in range(4)
                ]
                if all(
                    0 <= cell_row < Board.ROWS
                    and 0 <= cell_col < Board.COLS
                    and board.grid[cell_row][cell_col] == player
                    for cell_row, cell_col in cells
                ):
                    winners.add(player)
    assert len(winners) <= 1
    return next(iter(winners), 0)


@pytest.mark.parametrize(
    ("columns", "expected_player"),
    [
        ([0, 0, 1, 1, 2, 2, 3], 1),
        ([6, 0, 6, 1, 5, 2, 5, 3], 2),
        ([0, 1, 0, 1, 0, 1, 0], 1),
        ([1, 0, 1, 0, 2, 0, 2, 0], 2),
        ([3, 2, 2, 1, 1, 0, 1, 0, 0, 4, 0], 1),
        ([6, 3, 2, 2, 1, 1, 0, 1, 0, 0, 4, 0], 2),
        ([3, 4, 4, 5, 5, 6, 5, 6, 6, 2, 6], 1),
        ([0, 3, 4, 4, 5, 5, 6, 5, 6, 6, 2, 6], 2),
    ],
)
def test_winner_detects_every_line_for_both_players(
    columns: list[int], expected_player: int
) -> None:
    """Detect horizontal, vertical, and both diagonal wins for each player."""
    board = play(columns)

    assert board.winner() == expected_player
    cells = board.winning_cells()
    assert len(cells) == 4
    assert all(board.grid[row][col] == expected_player for row, col in cells)


def test_legal_moves_and_drop_follow_gravity() -> None:
    """Return ascending legal moves and place discs at the lowest open row."""
    board = Board()

    assert board.legal_moves() == list(range(7))
    assert board.drop(3) == 0
    assert board.drop(3) == 1
    assert board.grid[0][3] == 1
    assert board.grid[1][3] == 2


@pytest.mark.parametrize("column", [-1, 7, True, "3"])
def test_drop_rejects_invalid_columns(column: object) -> None:
    """Reject columns outside the board or with an invalid type."""
    with pytest.raises(ValueError):
        Board().drop(column)  # type: ignore[arg-type]


def test_drop_rejects_a_full_column() -> None:
    """Raise a clear error instead of overwriting a full column."""
    board = Board()
    for _ in range(Board.ROWS):
        board.drop(0)

    assert 0 not in board.legal_moves()
    with pytest.raises(ValueError, match="full"):
        board.drop(0)


def test_undo_restores_the_exact_previous_state() -> None:
    """Undo the newest move without affecting older board state."""
    board = play([3, 2, 3, 4])
    before_text = board.to_string()
    before_history = board.move_history.copy()

    board.drop(5)
    assert board.undo() == 5
    assert board.to_string() == before_text
    assert board.move_history == before_history

    clone = board.copy()
    clone.drop(6)
    assert clone.to_string() != board.to_string()


def test_current_player_alternates_from_move_count() -> None:
    """Derive the player to move solely from the number of moves made."""
    board = Board()

    assert board.current_player() == 1
    board.drop(0)
    assert board.current_player() == 2
    board.drop(1)
    assert board.current_player() == 1
    board.undo()
    assert board.current_player() == 2


def test_string_round_trip_and_terminal_draw() -> None:
    """Preserve text boards and identify a full board with no winner as a draw."""
    text = """\
OXOOXOO
OXXOXXO
OOXOOXO
XOXXOXX
XOOXOOX
XXOXXOX"""
    board = Board.from_string(text)

    assert board.to_string() == text
    assert board.is_full()
    assert board.winner() == 0
    assert board.is_terminal()


def test_from_string_rejects_floating_discs() -> None:
    """Reject impossible board text that violates gravity."""
    text = """\
.......
.......
.......
.......
X......
......."""

    with pytest.raises(ValueError, match="floating"):
        Board.from_string(text)


def test_seeded_random_playouts_match_a_full_board_winner_check() -> None:
    """Keep local winner detection correct through 1,000 deterministic games."""
    rng = random.Random(42)

    for _ in range(1_000):
        board = Board()
        while not board.is_terminal():
            legal_moves = board.legal_moves()
            assert legal_moves == sorted(legal_moves)
            assert all(board.grid[Board.ROWS - 1][col] == 0 for col in legal_moves)

            board.drop(rng.choice(legal_moves))
            assert board.winner() == slow_winner(board)
            assert set(cell for row in board.grid for cell in row) <= {0, 1, 2}

        assert board.winner() == slow_winner(board)
