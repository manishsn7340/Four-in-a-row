"""Plain fixed-depth Alpha-Beta search for Four in a Row."""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter

from agents.base import Agent, SearchStats
from agents.evaluation import evaluate
from agents.zobrist import EXACT, LOWER, UPPER, TTEntry, TranspositionTable
from config import MOVE_ORDER, WIN_SCORE
from game.board import Board


class _SearchTimeout(Exception):
    """Stop an unfinished Alpha-Beta search when its deadline is reached."""


class AlphaBetaAgent(Agent):
    """Choose moves with Minimax plus Alpha-Beta pruning."""

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
        """Create an Alpha-Beta agent with the selected v4 search options."""
        if isinstance(depth, bool) or not isinstance(depth, int) or depth < 1:
            raise ValueError("Depth must be a positive integer.")
        if not isinstance(use_ordering, bool):
            raise ValueError("use_ordering must be a boolean.")
        if not isinstance(use_iterative_deepening, bool):
            raise ValueError("use_iterative_deepening must be a boolean.")
        if time_limit is not None and (
            isinstance(time_limit, bool) or not isinstance(time_limit, (int, float))
        ):
            raise ValueError("time_limit must be a positive number or None.")
        if time_limit is not None and time_limit <= 0:
            raise ValueError("time_limit must be a positive number or None.")
        if not isinstance(use_tt, bool):
            raise ValueError("use_tt must be a boolean.")

        super().__init__(name or f"Alpha-Beta (depth {depth})")
        self.depth = depth
        self.use_ordering = use_ordering
        self.use_iterative_deepening = use_iterative_deepening
        self.time_limit = float(time_limit) if time_limit is not None else None
        self.use_tt = use_tt
        self.weights = weights
        self._deadline: float | None = None
        self._table: TranspositionTable | None = (
            TranspositionTable() if use_tt else None
        )

    def choose_move(self, board: Board) -> int:
        """Return the best legal column while restoring ``board`` before returning."""
        start = perf_counter()
        self.last_stats = SearchStats()
        legal_moves = board.legal_moves()
        if not legal_moves:
            raise ValueError("Cannot choose a move on a full board.")

        root_player = board.current_player()
        if self._table is not None:
            self._table.set_root_player(root_player)
        fallback_move = legal_moves[0]
        self._deadline = (
            start + self.time_limit if self.time_limit is not None else None
        )
        try:
            if self.use_iterative_deepening:
                return self._choose_iteratively(board, root_player, fallback_move)
            return self._choose_fixed_depth(board, root_player)
        except _SearchTimeout:
            self.last_stats.best_move = fallback_move
            return fallback_move
        finally:
            self.last_stats.time_s = perf_counter() - start
            self._deadline = None

    def _choose_fixed_depth(self, board: Board, root_player: int) -> int:
        """Complete one fixed-depth Alpha-Beta search from the root."""
        move, score = self._search_root(board, self.depth, root_player)
        self.last_stats.best_move = move
        self.last_stats.score = score
        self.last_stats.depth_reached = self.depth
        return move

    def _choose_iteratively(
        self, board: Board, root_player: int, fallback_move: int
    ) -> int:
        """Search increasing depths and keep the last fully completed result."""
        best_move = fallback_move
        best_score: float | None = None
        previous_best: int | None = None
        for current_depth in range(1, self.depth + 1):
            try:
                move, score = self._search_root(
                    board, current_depth, root_player, previous_best
                )
            except _SearchTimeout:
                break

            best_move = move
            best_score = score
            previous_best = move
            self.last_stats.best_move = move
            self.last_stats.score = score
            self.last_stats.depth_reached = current_depth
            self._report_progress(current_depth, move, score)
            if abs(score) >= WIN_SCORE:
                break

        self.last_stats.best_move = best_move
        self.last_stats.score = best_score
        return best_move

    def _search_root(
        self,
        board: Board,
        depth: int,
        root_player: int,
        preferred_move: int | None = None,
    ) -> tuple[int, float]:
        """Search root moves with a running alpha value and strict tie-breaking."""
        alpha = float("-inf")
        beta = float("inf")
        original_alpha = alpha
        original_beta = beta
        entry = self._table_entry(board.hash)
        if entry is not None and entry.depth >= depth and entry.flag == EXACT:
            self.last_stats.tt_hits += 1
            return entry.best_move or board.legal_moves()[0], entry.score

        tt_move = entry.best_move if entry is not None else None
        preferred = preferred_move if preferred_move is not None else tt_move
        ordered_moves = self._ordered_moves(board.legal_moves(), preferred)
        best_move = ordered_moves[0]
        best_score = float("-inf")
        column_scores: dict[int, float] = {}
        for col in ordered_moves:
            board.drop(col)
            try:
                score = self._alphabeta(
                    board, depth - 1, False, root_player, alpha, beta
                )
            finally:
                board.undo()

            column_scores[col] = score
            if score > best_score:
                best_score = score
                best_move = col
            alpha = max(alpha, best_score)
        self.last_stats.column_scores = column_scores
        self._store_table_entry(
            board.hash,
            depth,
            best_score,
            original_alpha,
            original_beta,
            best_move,
        )
        return best_move, best_score

    def _alphabeta(
        self,
        board: Board,
        depth: int,
        maximizing: bool,
        root_player: int,
        alpha: float,
        beta: float,
    ) -> float:
        """Return a Minimax score while pruning branches that cannot matter."""
        self.last_stats.nodes += 1
        self._check_timeout()
        original_alpha = alpha
        original_beta = beta
        entry = self._table_entry(board.hash)
        preferred_move = entry.best_move if entry is not None else None
        if entry is not None and entry.depth >= depth:
            if entry.flag == EXACT:
                self.last_stats.tt_hits += 1
                return entry.score
            if entry.flag == LOWER:
                alpha = max(alpha, entry.score)
            if entry.flag == UPPER:
                beta = min(beta, entry.score)
            if alpha >= beta:
                self.last_stats.tt_hits += 1
                return entry.score

        winner = board.winner()
        if winner == root_player:
            return float(WIN_SCORE + depth)
        if winner != 0:
            return float(-(WIN_SCORE + depth))
        if board.is_full():
            return 0.0
        if depth == 0:
            score = float(evaluate(board, root_player, self.weights))
            self._store_table_entry(
                board.hash,
                depth,
                score,
                original_alpha,
                original_beta,
                None,
            )
            return score

        if maximizing:
            best = float("-inf")
            best_move: int | None = None
            for col in self._ordered_moves(board.legal_moves(), preferred_move):
                board.drop(col)
                try:
                    value = self._alphabeta(
                        board, depth - 1, False, root_player, alpha, beta
                    )
                finally:
                    board.undo()
                if value > best:
                    best = value
                    best_move = col
                alpha = max(alpha, best)
                if alpha >= beta:
                    self.last_stats.cutoffs += 1
                    break
            self._store_table_entry(
                board.hash,
                depth,
                best,
                original_alpha,
                original_beta,
                best_move,
            )
            return best

        best = float("inf")
        best_move = None
        for col in self._ordered_moves(board.legal_moves(), preferred_move):
            board.drop(col)
            try:
                value = self._alphabeta(
                    board, depth - 1, True, root_player, alpha, beta
                )
            finally:
                board.undo()
            if value < best:
                best = value
                best_move = col
            beta = min(beta, best)
            if alpha >= beta:
                self.last_stats.cutoffs += 1
                break
        self._store_table_entry(
            board.hash,
            depth,
            best,
            original_alpha,
            original_beta,
            best_move,
        )
        return best

    def _table_entry(self, key: int) -> TTEntry | None:
        """Return a cached entry when transposition tables are enabled."""
        return self._table.get(key) if self._table is not None else None

    def _store_table_entry(
        self,
        key: int,
        depth: int,
        score: float,
        original_alpha: float,
        original_beta: float,
        best_move: int | None,
    ) -> None:
        """Classify and store one Alpha-Beta result when caching is enabled."""
        if self._table is None:
            return
        if score <= original_alpha:
            flag = UPPER
        elif score >= original_beta:
            flag = LOWER
        else:
            flag = EXACT
        self._table.store(key, depth, score, flag, best_move)

    def _ordered_moves(
        self, legal_moves: list[int], preferred_move: int | None = None
    ) -> list[int]:
        """Return legal moves in plain or center-first order with an optional hint."""
        moves = legal_moves.copy()
        preferred: list[int] = []
        if preferred_move in moves:
            moves.remove(preferred_move)
            preferred.append(preferred_move)

        if self.use_ordering:
            legal_set = set(moves)
            moves = [col for col in MOVE_ORDER if col in legal_set]
        return preferred + moves

    def _check_timeout(self) -> None:
        """Raise _SearchTimeout every 1,024 visited nodes after the deadline."""
        if (
            self._deadline is not None
            and self.last_stats.nodes % 1_024 == 0
            and perf_counter() >= self._deadline
        ):
            raise _SearchTimeout

    def _report_progress(self, depth: int, move: int, score: float) -> None:
        """Send one small update after an iterative depth finishes."""
        if self.on_progress is not None:
            self.on_progress(
                {
                    "depth": depth,
                    "best_move": move,
                    "score": score,
                    "nodes": self.last_stats.nodes,
                    "cutoffs": self.last_stats.cutoffs,
                    "column_scores": dict(self.last_stats.column_scores or {}),
                }
            )
