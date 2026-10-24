"""Fixed-depth Minimax search for Four in a Row."""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter

from agents.base import Agent, SearchStats
from agents.evaluation import evaluate
from config import WIN_SCORE
from game.board import Board


class MinimaxAgent(Agent):
    """Choose moves with readable fixed-depth Minimax search."""

    def __init__(
        self,
        depth: int = 4,
        weights: Mapping[str, int] | None = None,
        name: str | None = None,
    ) -> None:
        """Create a Minimax agent that searches ``depth`` plies from the root."""
        if isinstance(depth, bool) or not isinstance(depth, int) or depth < 1:
            raise ValueError("Depth must be a positive integer.")
        super().__init__(name or f"Minimax (depth {depth})")
        self.depth = depth
        self.weights = weights

    def choose_move(self, board: Board) -> int:
        """Return the best legal column while restoring ``board`` before returning."""
        start = perf_counter()
        self.last_stats = SearchStats()
        legal_moves = board.legal_moves()
        if not legal_moves:
            raise ValueError("Cannot choose a move on a full board.")

        root_player = board.current_player()
        best_move = legal_moves[0]
        best_score = float("-inf")
        try:
            for col in legal_moves:
                board.drop(col)
                try:
                    score = self._minimax(
                        board, self.depth - 1, False, root_player
                    )
                finally:
                    board.undo()
                if score > best_score:
                    best_score = score
                    best_move = col

            self.last_stats.best_move = best_move
            self.last_stats.score = best_score
            self.last_stats.depth_reached = self.depth
            return best_move
        finally:
            self.last_stats.time_s = perf_counter() - start

    def _minimax(
        self, board: Board, depth: int, maximizing: bool, root_player: int
    ) -> float:
        """Score a position with explicit MAX and MIN branches."""
        self.last_stats.nodes += 1
        winner = board.winner()
        if winner == root_player:
            return float(WIN_SCORE + depth)
        if winner != 0:
            return float(-(WIN_SCORE + depth))
        if board.is_full():
            return 0.0
        if depth == 0:
            return float(evaluate(board, root_player, self.weights))

        if maximizing:
            best = float("-inf")
            for col in board.legal_moves():
                board.drop(col)
                try:
                    best = max(
                        best,
                        self._minimax(board, depth - 1, False, root_player),
                    )
                finally:
                    board.undo()
            return best

        best = float("inf")
        for col in board.legal_moves():
            board.drop(col)
            try:
                best = min(
                    best,
                    self._minimax(board, depth - 1, True, root_player),
                )
            finally:
                board.undo()
        return best
