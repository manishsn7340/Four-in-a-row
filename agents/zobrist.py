"""Deterministic Zobrist hashing and bounded transposition-table storage."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final

from config import COLS, ROWS, TT_MAX_ENTRIES, ZOBRIST_SEED


EXACT: Final[str] = "EXACT"
LOWER: Final[str] = "LOWER"
UPPER: Final[str] = "UPPER"


class Zobrist:
    """Hold one deterministic 64-bit key for each board cell and player."""

    def __init__(self, seed: int = ZOBRIST_SEED) -> None:
        """Generate a reproducible table using an isolated seeded generator."""
        rng = random.Random(seed)
        self.keys: tuple[tuple[tuple[int, int], ...], ...] = tuple(
            tuple(
                (rng.getrandbits(64), rng.getrandbits(64))
                for _ in range(COLS)
            )
            for _ in range(ROWS)
        )

    def key_for(self, row: int, col: int, player: int) -> int:
        """Return the key assigned to ``player`` occupying one board cell."""
        if player not in (1, 2):
            raise ValueError("Player must be 1 or 2.")
        return self.keys[row][col][player - 1]


ZOBRIST: Final[Zobrist] = Zobrist()
ZOBRIST_TABLE: Final[tuple[tuple[tuple[int, int], ...], ...]] = ZOBRIST.keys


def zobrist_key(row: int, col: int, player: int) -> int:
    """Return the shared deterministic Zobrist key for one occupied cell."""
    return ZOBRIST.key_for(row, col, player)


@dataclass(frozen=True)
class TTEntry:
    """Store an Alpha-Beta result for one hashed position."""

    key: int
    depth: int
    score: float
    flag: str
    best_move: int | None


class TranspositionTable:
    """Bound cached search results, refusing new entries once full."""

    def __init__(self, max_entries: int = TT_MAX_ENTRIES) -> None:
        """Create an empty table with a fixed maximum number of entries."""
        if isinstance(max_entries, bool) or not isinstance(max_entries, int):
            raise ValueError("max_entries must be a positive integer.")
        if max_entries < 1:
            raise ValueError("max_entries must be a positive integer.")
        self.max_entries = max_entries
        self.root_player: int | None = None
        self._entries: dict[int, TTEntry] = {}

    def __len__(self) -> int:
        """Return the number of cached positions currently stored."""
        return len(self._entries)

    def clear(self) -> None:
        """Remove every cached position while retaining the configured limit."""
        self._entries.clear()

    def set_root_player(self, player: int) -> None:
        """Clear cached scores if their root-player perspective changes."""
        if player not in (1, 2):
            raise ValueError("Player must be 1 or 2.")
        if self.root_player != player:
            self.clear()
            self.root_player = player

    def get(self, key: int) -> TTEntry | None:
        """Return the entry for ``key`` when one is cached."""
        return self._entries.get(key)

    def store(
        self, key: int, depth: int, score: float, flag: str, best_move: int | None
    ) -> None:
        """Store a deeper entry, or refuse a new entry when the table is full."""
        if flag not in (EXACT, LOWER, UPPER):
            raise ValueError("flag must be EXACT, LOWER, or UPPER.")

        existing = self._entries.get(key)
        if existing is not None:
            if depth >= existing.depth:
                self._entries[key] = TTEntry(key, depth, score, flag, best_move)
            return
        if len(self) >= self.max_entries:
            return
        self._entries[key] = TTEntry(key, depth, score, flag, best_move)
