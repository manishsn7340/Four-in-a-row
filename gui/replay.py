"""gui/replay.py — Game replay state manager.

Records every move played in a game as a list of columns.
The replay controller can scrub to any step by re-applying moves from scratch.
Also supports exporting the game to a text file.
"""

from __future__ import annotations

import datetime
import pathlib

from game.board import Board


class ReplayManager:
    """Captures the move log and generates Board snapshots for replay scrubbing."""

    def __init__(self) -> None:
        self.moves: list[int] = []  # full game move history (columns, 0-indexed)
        self._scrub_step: int = 0
        self.active: bool = False   # True once game is over and replay is available

    def record(self, col: int) -> None:
        """Append one move to the log."""
        self.moves.append(col)

    def clear(self) -> None:
        """Start fresh for a new game."""
        self.moves = []
        self._scrub_step = 0
        self.active = False

    def activate(self) -> None:
        """Mark the game as finished so the replay slider appears."""
        self.active = True
        self._scrub_step = len(self.moves)  # start at the final position

    @property
    def total_moves(self) -> int:
        return len(self.moves)

    @property
    def step(self) -> int:
        return self._scrub_step

    @step.setter
    def step(self, value: int) -> None:
        self._scrub_step = max(0, min(len(self.moves), value))

    def board_at_step(self, step: int | None = None) -> Board:
        """Reconstruct and return the Board at a given step (default = current scrub_step)."""
        target = step if step is not None else self._scrub_step
        b = Board()
        for col in self.moves[:target]:
            b.drop(col)
        return b

    def export(self, out_dir: str = "results") -> str:
        """Save the game to a text file and return the path."""
        path = pathlib.Path(out_dir)
        path.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = path / f"game_{ts}.txt"
        with open(fname, "w") as f:
            f.write("# Connect Four Lab — Game Record\n")
            f.write(f"# Date: {ts}\n")
            f.write(f"# Moves ({len(self.moves)} total):\n")
            f.write("moves: " + " ".join(str(m) for m in self.moves) + "\n")
        return str(fname)
