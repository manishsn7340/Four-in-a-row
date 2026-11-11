"""Alpha-Beta search with optional move ordering, iterative deepening and a
transposition table. Each feature can be switched off for the ablation study."""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter

from agents.base import Agent, SearchStats
from agents.evaluation import evaluate
from agents.zobrist import EXACT, LOWER, UPPER, TranspositionTable
from config import MOVE_ORDER, WIN_SCORE
from game.board import Board

INF = float("inf")


class _Timeout(Exception):
    pass


class AlphaBetaAgent(Agent):
    def __init__(
        self,
        depth: int = 6,
        use_ordering: bool = True,
        use_iterative_deepening: bool = False,
        time_limit: float | None = None,
        use_tt: bool = False,
        weights: Mapping[str, int] | None = None,
        name: str | None = None,
    ) -> None:
        if type(depth) is not int or depth < 1:
            raise ValueError("Depth must be a positive integer.")
        super().__init__(name or f"Alpha-Beta (depth {depth})")
        self.depth = depth
        self.use_ordering = use_ordering
        self.use_iterative_deepening = use_iterative_deepening
        self.time_limit = time_limit
        self.use_tt = use_tt
        self.weights = weights
        self._table = TranspositionTable() if use_tt else None
        self._deadline: float | None = None

    def choose_move(self, board: Board) -> int:
        start = perf_counter()
        self.last_stats = stats = SearchStats()
        me = board.current_player()
        if self._table:
            self._table.set_root_player(me)
        self._deadline = start + self.time_limit if self.time_limit else None

        best_move = board.legal_moves()[0]  # fallback if time runs out at depth 1
        previous = None
        depths = range(1, self.depth + 1) if self.use_iterative_deepening else [self.depth]
        try:
            for depth in depths:
                # Search the previous depth's best move first: it is usually still best.
                best_move, stats.score = self._search_root(board, depth, me, previous)
                previous = best_move
                stats.depth_reached = depth
                self._report_progress(depth, best_move)
                if abs(stats.score) >= WIN_SCORE:
                    break
        except _Timeout:
            pass  # keep the result of the last fully completed depth
        stats.best_move = best_move
        stats.time_s = perf_counter() - start
        return best_move

    def _search_root(self, board: Board, depth: int, me: int,
                     previous: int | None) -> tuple[int, float]:
        entry = self._table.get(board.hash) if self._table else None
        if entry and entry.depth >= depth and entry.flag == EXACT:
            self.last_stats.tt_hits += 1
            return entry.best_move, entry.score

        alpha = -INF
        best_move, best_score = None, -INF
        scores = {}
        if previous is None and entry:
            previous = entry.best_move
        for col in self._ordered(board, previous):
            board.drop(col)
            try:
                scores[col] = self._alphabeta(board, depth - 1, False, me, alpha, INF)
            finally:
                board.undo()
            if scores[col] > best_score:
                best_move, best_score = col, scores[col]
            alpha = max(alpha, best_score)
        self.last_stats.column_scores = scores
        self._store(board.hash, depth, best_score, -INF, INF, best_move)
        return best_move, best_score

    def _alphabeta(self, board: Board, depth: int, maximizing: bool, me: int,
                   alpha: float, beta: float) -> float:
        stats = self.last_stats
        stats.nodes += 1
        if self._deadline and stats.nodes % 1024 == 0 and perf_counter() >= self._deadline:
            raise _Timeout

        alpha0, beta0 = alpha, beta
        entry = self._table.get(board.hash) if self._table else None
        if entry and entry.depth >= depth:
            if entry.flag == EXACT:
                stats.tt_hits += 1
                return entry.score
            if entry.flag == LOWER:
                alpha = max(alpha, entry.score)
            else:
                beta = min(beta, entry.score)
            if alpha >= beta:
                stats.tt_hits += 1
                return entry.score

        winner = board.winner()
        if winner:
            return float(WIN_SCORE + depth) * (1 if winner == me else -1)
        if board.is_full():
            return 0.0
        if depth == 0:
            score = float(evaluate(board, me, self.weights))
            self._store(board.hash, 0, score, alpha0, beta0, None)
            return score

        best, best_move = (-INF if maximizing else INF), None
        for col in self._ordered(board, entry.best_move if entry else None):
            board.drop(col)
            try:
                value = self._alphabeta(board, depth - 1, not maximizing, me, alpha, beta)
            finally:
                board.undo()
            if (value > best) if maximizing else (value < best):
                best, best_move = value, col
            if maximizing:
                alpha = max(alpha, best)
            else:
                beta = min(beta, best)
            if alpha >= beta:
                stats.cutoffs += 1
                break
        self._store(board.hash, depth, best, alpha0, beta0, best_move)
        return best

    def _store(self, key: int, depth: int, score: float, alpha0: float, beta0: float,
               best_move: int | None) -> None:
        """Record a result, labelled by how it relates to the original alpha-beta window."""
        if self._table is None:
            return
        flag = UPPER if score <= alpha0 else LOWER if score >= beta0 else EXACT
        self._table.store(key, depth, score, flag, best_move)

    def _ordered(self, board: Board, first: int | None) -> list[int]:
        """Legal moves, centre-first if ordering is on, with `first` moved to the front."""
        moves = board.legal_moves()
        if self.use_ordering:
            moves = [c for c in MOVE_ORDER if c in moves]
        if first in moves:
            moves.remove(first)
            moves.insert(0, first)
        return moves

    def _report_progress(self, depth: int, move: int) -> None:
        if self.on_progress:
            s = self.last_stats
            self.on_progress({"depth": depth, "best_move": move, "score": s.score,
                              "nodes": s.nodes, "cutoffs": s.cutoffs,
                              "column_scores": dict(s.column_scores or {})})
