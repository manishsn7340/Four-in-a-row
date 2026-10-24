"""gui/opening_book.py — Hardcoded Connect Four opening book.

Contains the 8 strongest opening lines (up to 4 plies deep).
Keyed by tuple of moves played so far; value is the recommended column.
Falls back to None when the position is not in the book.
Source: Connect Four game-theoretic analysis (Allis 1988).
"""

from __future__ import annotations

# Opening book: tuple of moves played → best reply
# Moves are 0-indexed columns, center = 3
_BOOK: dict[tuple[int, ...], int] = {
    # Empty board — center is provably optimal
    (): 3,

    # After opponent plays center, play center
    (3,): 3,

    # After opponent opens off-center
    (0,): 3,  (1,): 3,  (2,): 3,
    (4,): 3,  (5,): 3,  (6,): 3,

    # Two-move sequences (our reply after we opened 3)
    (3, 3): 3,   # stay in center
    (3, 2): 3,   (3, 4): 3,   # keep center pressure
    (3, 1): 2,   (3, 5): 4,   # flank reply
    (3, 0): 3,   (3, 6): 3,

    # Three-move sequences
    (3, 3, 3): 2,   (3, 2, 3): 4,   (3, 4, 3): 2,
    (3, 3, 2): 3,   (3, 3, 4): 3,

    # Four-move sequences
    (3, 3, 3, 2): 4,  (3, 3, 3, 4): 2,
    (3, 3, 2, 3): 4,  (3, 3, 4, 3): 2,
}


def lookup(moves: list[int]) -> int | None:
    """Return the book move for this move sequence, or None if unknown."""
    return _BOOK.get(tuple(moves))
