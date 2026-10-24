"""Project-wide constants for the Four in a Row AI project."""

from typing import Final

ROWS: Final[int] = 6
COLS: Final[int] = 7
WIN_SCORE: Final[int] = 1_000_000
MOVE_ORDER: Final[tuple[int, ...]] = (3, 2, 4, 1, 5, 0, 6)
DEFAULT_TIME_LIMIT: Final[float] = 1.0
TT_MAX_ENTRIES: Final[int] = 1_000_000
ZOBRIST_SEED: Final[int] = 42
MCTS_C: Final[float] = 1.41
GLOBAL_SEED: Final[int] = 42
