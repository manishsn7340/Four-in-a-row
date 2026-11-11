"""Tests for Zobrist hashing and the transposition table."""

from __future__ import annotations

import pytest

from agents.alphabeta import AlphaBetaAgent
from agents.zobrist import EXACT, LOWER, UPPER, TranspositionTable, Zobrist
from config import TT_MAX_ENTRIES
from game.board import Board
from helpers import seeded_positions, snapshot


def test_zobrist_keys_are_seeded_and_hash_tracks_drops_and_undos() -> None:
    """Use repeatable keys and restore the initial hash after undoing moves."""
    first = Zobrist(seed=123)
    second = Zobrist(seed=123)
    different = Zobrist(seed=456)
    board = Board()
    initial_hash = board.hash

    assert first.keys == second.keys
    assert first.keys != different.keys

    for column in (3, 2, 3, 5, 0, 2):
        board.drop(column)
        assert board.hash == board._calculate_hash()

    while board.move_history:
        board.undo()
        assert board.hash == board._calculate_hash()
    assert board.hash == initial_hash


def test_different_move_orders_for_same_position_have_the_same_hash() -> None:
    """Hash only the position because the side to move follows disc count."""
    first = Board()
    second = Board()
    for column in (0, 1, 2, 3, 4, 5):
        first.drop(column)
    for column in (2, 1, 0, 3, 4, 5):
        second.drop(column)

    assert first.to_string() == second.to_string()
    assert first.current_player() == second.current_player()
    assert first.hash == second.hash


def test_transposition_table_replaces_deeper_entries_and_respects_capacity() -> None:
    """Keep the deepest value for a key and never exceed the configured limit."""
    table = TranspositionTable(max_entries=2)
    table.store(1, 3, 10.0, EXACT, 4)
    table.store(1, 2, 20.0, LOWER, 5)
    table.store(1, 4, 30.0, UPPER, 6)
    table.store(2, 1, 5.0, EXACT, 3)
    table.store(3, 1, 1.0, EXACT, 0)

    assert table.get(1) is not None
    assert table.get(1).depth == 4
    assert table.get(1).score == 30.0
    assert table.get(1).flag == UPPER
    assert table.get(1).best_move == 6
    assert table.get(3) is None
    assert len(table) == 2
    assert len(table) <= table.max_entries
    assert TranspositionTable().max_entries == TT_MAX_ENTRIES


def test_transposition_table_clears_when_root_player_changes() -> None:
    """Do not reuse scores calculated from a different player's perspective."""
    table = TranspositionTable()
    table.set_root_player(1)
    table.store(42, 2, 12.0, EXACT, 3)

    table.set_root_player(2)

    assert table.root_player == 2
    assert table.get(42) is None
    assert len(table) == 0


def test_transposition_table_rejects_invalid_flags() -> None:
    """Reject entries whose bound type cannot be interpreted by search."""
    table = TranspositionTable()

    with pytest.raises(ValueError, match="flag"):
        table.store(1, 1, 0.0, "INVALID", None)


def test_alpha_beta_with_tt_matches_without_tt_on_seeded_positions() -> None:
    """Preserve the root score when cached exact and bound results are reused."""
    for position in seeded_positions(30, 161803, 6, 18):
        before = snapshot(position)
        plain = AlphaBetaAgent(depth=5, use_ordering=True)
        cached = AlphaBetaAgent(depth=5, use_ordering=True, use_tt=True)

        plain_move = plain.choose_move(position)
        cached_move = cached.choose_move(position)

        assert cached_move in position.legal_moves()
        assert cached.last_stats.score == plain.last_stats.score
        assert cached.last_stats.nodes <= plain.last_stats.nodes
        assert snapshot(position) == before


def test_alpha_beta_tt_hits_and_reduces_nodes_on_repeated_positions() -> None:
    """Reuse transposed positions during search instead of expanding them again."""
    position = Board()
    before = snapshot(position)
    plain = AlphaBetaAgent(depth=8, use_ordering=True)
    cached = AlphaBetaAgent(depth=8, use_ordering=True, use_tt=True)

    plain.choose_move(position)
    cached_move = cached.choose_move(position)

    assert cached_move in position.legal_moves()
    assert cached.last_stats.score == plain.last_stats.score
    assert cached.last_stats.tt_hits > 0
    assert cached.last_stats.nodes < plain.last_stats.nodes
    assert snapshot(position) == before
