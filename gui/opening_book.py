"""Opening book: the recommended reply for the first few moves (column 3 is the centre).

Centre-first play is optimal for the first player (Allis, 1988)."""

from __future__ import annotations

BOOK: dict[tuple[int, ...], int] = {
    (): 3,
    (0,): 3, (1,): 3, (2,): 3, (3,): 3, (4,): 3, (5,): 3, (6,): 3,
    (3, 0): 3, (3, 1): 2, (3, 2): 3, (3, 3): 3, (3, 4): 3, (3, 5): 4, (3, 6): 3,
    (3, 3, 3): 2, (3, 2, 3): 4, (3, 4, 3): 2, (3, 3, 2): 3, (3, 3, 4): 3,
    (3, 3, 3, 2): 4, (3, 3, 3, 4): 2, (3, 3, 2, 3): 4, (3, 3, 4, 3): 2,
}


def lookup(moves: list[int]) -> int | None:
    return BOOK.get(tuple(moves))
