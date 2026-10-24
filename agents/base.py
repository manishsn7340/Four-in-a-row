"""Shared agent interface and statistics for Four in a Row opponents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from game.board import Board


@dataclass
class SearchStats:
    """Record measurements from one completed agent move selection."""

    nodes: int = 0
    cutoffs: int = 0
    tt_hits: int = 0
    time_s: float = 0.0
    depth_reached: int = 0
    score: float | None = None
    best_move: int | None = None
    simulations: int = 0
    column_scores: dict[int, float] | None = None


class Agent:
    """Base class for every interchangeable Four in a Row opponent."""

    def __init__(self, name: str) -> None:
        """Create an agent with empty statistics and no progress callback."""
        self.name = name
        self.last_stats = SearchStats()
        self.on_progress: Callable[[dict], None] | None = None

    def choose_move(self, board: Board) -> int:
        """Return a legal column without changing the supplied board."""
        raise NotImplementedError("Subclasses must implement choose_move().")
