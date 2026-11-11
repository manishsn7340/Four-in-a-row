"""Plain fixed-depth Minimax: the baseline that Alpha-Beta must agree with."""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter

from agents.base import Agent, SearchStats
from agents.evaluation import evaluate
from config import WIN_SCORE
from game.board import Board


class MinimaxAgent(Agent):
    def __init__(self, depth: int = 4, weights: Mapping[str, int] | None = None,
                 name: str | None = None) -> None:
        if type(depth) is not int or depth < 1:
            raise ValueError("Depth must be a positive integer.")
        super().__init__(name or f"Minimax (depth {depth})")
        self.depth = depth
        self.weights = weights

    def choose_move(self, board: Board) -> int:
        start = perf_counter()
        self.last_stats = SearchStats(depth_reached=self.depth)
        me = board.current_player()
        best_move, best_score = None, float("-inf")
        for col in board.legal_moves():
            board.drop(col)
            score = self._minimax(board, self.depth - 1, False, me)
            board.undo()
            if score > best_score:
                best_move, best_score = col, score
        self.last_stats.best_move = best_move
        self.last_stats.score = best_score
        self.last_stats.time_s = perf_counter() - start
        return best_move

    def _minimax(self, board: Board, depth: int, maximizing: bool, me: int) -> float:
        self.last_stats.nodes += 1
        winner = board.winner()
        if winner:
            # Adding the remaining depth makes faster wins (and slower losses) score better.
            return float(WIN_SCORE + depth) * (1 if winner == me else -1)
        if board.is_full():
            return 0.0
        if depth == 0:
            return float(evaluate(board, me, self.weights))

        scores = []
        for col in board.legal_moves():
            board.drop(col)
            scores.append(self._minimax(board, depth - 1, not maximizing, me))
            board.undo()
        return max(scores) if maximizing else min(scores)
