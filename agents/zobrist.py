"""Zobrist hashing and a size-limited transposition table for Alpha-Beta."""

from __future__ import annotations

import random
from dataclasses import dataclass

from config import COLS, ROWS, TT_MAX_ENTRIES, ZOBRIST_SEED

# Bound types: EXACT score, LOWER bound (score >= value), UPPER bound (score <= value).
EXACT, LOWER, UPPER = "EXACT", "LOWER", "UPPER"


class Zobrist:
    """One random 64-bit number per (cell, player); a position's hash XORs its discs."""

    def __init__(self, seed: int = ZOBRIST_SEED) -> None:
        rng = random.Random(seed)
        self.keys = tuple(
            tuple((rng.getrandbits(64), rng.getrandbits(64)) for _ in range(COLS))
            for _ in range(ROWS)
        )


_KEYS = Zobrist().keys


def zobrist_key(row: int, col: int, player: int) -> int:
    return _KEYS[row][col][player - 1]


@dataclass(frozen=True)
class TTEntry:
    key: int
    depth: int
    score: float
    flag: str
    best_move: int | None


class TranspositionTable:
    """Cache of search results. Deeper results replace shallower ones; when full,
    new positions are simply not stored."""

    def __init__(self, max_entries: int = TT_MAX_ENTRIES) -> None:
        self.max_entries = max_entries
        self.root_player: int | None = None
        self._entries: dict[int, TTEntry] = {}

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def set_root_player(self, player: int) -> None:
        """Scores are stored from the root player's view, so a new root player
        invalidates everything."""
        if player != self.root_player:
            self.clear()
            self.root_player = player

    def get(self, key: int) -> TTEntry | None:
        return self._entries.get(key)

    def store(self, key: int, depth: int, score: float, flag: str, best_move: int | None) -> None:
        if flag not in (EXACT, LOWER, UPPER):
            raise ValueError(f"Unknown flag {flag!r}.")
        old = self._entries.get(key)
        if old is None and len(self._entries) >= self.max_entries:
            return
        if old is None or depth >= old.depth:
            self._entries[key] = TTEntry(key, depth, score, flag, best_move)
