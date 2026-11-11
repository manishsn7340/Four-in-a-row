"""Baseline opponents: a seeded random player and a one-move-lookahead greedy player."""

from __future__ import annotations

import random
from time import perf_counter

from agents.base import Agent, SearchStats
from config import GLOBAL_SEED, MOVE_ORDER, WIN_SCORE
from game.board import Board


class RandomAgent(Agent):
    def __init__(self, seed: int = GLOBAL_SEED, name: str | None = None) -> None:
        super().__init__(name or "Random")
        self._rng = random.Random(seed)

    def choose_move(self, board: Board) -> int:
        start = perf_counter()
        move = self._rng.choice(board.legal_moves())
        self.last_stats = SearchStats(time_s=perf_counter() - start, best_move=move)
        return move


class GreedyAgent(Agent):
    """Win if possible, otherwise block, otherwise play nearest the centre."""

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name or "Greedy")

    def choose_move(self, board: Board) -> int:
        start = perf_counter()
        me = board.current_player()
        moves = [c for c in MOVE_ORDER if c in board.legal_moves()]
        wins = [c for c in moves if board.would_win(c, me)]
        blocks = [c for c in moves if board.would_win(c, 3 - me)]
        move = (wins or blocks or moves)[0]
        score = WIN_SCORE if wins else 0
        self.last_stats = SearchStats(time_s=perf_counter() - start, best_move=move, score=score)
        return move
