"""Monte Carlo Tree Search agent for Four in a Row."""

from __future__ import annotations

import math
import random
from time import perf_counter

from agents.base import Agent, SearchStats
from config import MCTS_C
from game.board import Board


class _Node:
    """Single MCTS tree node."""

    __slots__ = ("move", "parent", "children", "untried_moves", "visits", "wins", "to_move")

    def __init__(self, board: Board, move: int | None, parent: "_Node | None") -> None:
        self.move = move                     # column that led to this node
        self.parent = parent
        self.children: list[_Node] = []
        self.untried_moves: list[int] = board.legal_moves()
        self.visits = 0
        self.wins = 0.0
        self.to_move = board.current_player()  # player whose turn it is at this node

    def ucb1(self, c: float) -> float:
        """UCB1 score for selection."""
        if self.visits == 0:
            return float("inf")
        return self.wins / self.visits + c * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

    def best_child(self, c: float) -> "_Node":
        return max(self.children, key=lambda n: n.ucb1(c))

    def most_visited(self) -> "_Node":
        return max(self.children, key=lambda n: n.visits)

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0


class MCTSAgent(Agent):
    """Choose moves with Monte Carlo Tree Search."""

    def __init__(
        self,
        simulations: int = 2000,
        time_limit: float | None = None,
        c: float = MCTS_C,
        rollout: str = "random",
        seed: int = 42,
        name: str | None = None,
    ) -> None:
        super().__init__(name or f"MCTS (sims={simulations})")
        self.simulations = simulations
        self.time_limit = time_limit
        self.c = c
        self.rollout = rollout
        self.rng = random.Random(seed)

    def choose_move(self, board: Board) -> int:
        """Return the best column; board is not modified."""
        start = perf_counter()
        self.last_stats = SearchStats()
        root_player = board.current_player()

        # Fast path: take an immediate win
        for col in board.legal_moves():
            board.drop(col)
            won = board.winner() != 0
            board.undo()
            if won:
                self.last_stats.best_move = col
                self.last_stats.simulations = 0
                return col

        root = _Node(board, None, None)
        sim_count = 0

        while True:
            if self.time_limit is not None and perf_counter() - start >= self.time_limit:
                break
            if self.time_limit is None and sim_count >= self.simulations:
                break

            b = board.copy()
            node = self._select(root, b)
            node = self._expand(node, b)
            result = self._rollout(b, root_player)
            self._backpropagate(node, result, root_player)
            sim_count += 1

            if sim_count % 200 == 0 and self.on_progress is not None:
                bm = root.most_visited().move if root.children else None
                self.on_progress({"simulations": sim_count, "best_move": bm})

        best = root.most_visited()
        self.last_stats.simulations = sim_count
        self.last_stats.best_move = best.move
        self.last_stats.time_s = perf_counter() - start
        self.last_stats.column_scores = {
            child.move: child.wins / child.visits if child.visits > 0 else 0.0
            for child in root.children
        }
        return best.move

    # ------------------------------------------------------------------

    def _select(self, node: _Node, board: Board) -> _Node:
        """Descend via UCB1 until a node has untried moves."""
        while node.is_fully_expanded() and node.children:
            node = node.best_child(self.c)
            board.drop(node.move)
        return node

    def _expand(self, node: _Node, board: Board) -> _Node:
        """Add one new child by picking a random untried move."""
        if board.is_terminal() or not node.untried_moves:
            return node
        move = self.rng.choice(node.untried_moves)
        node.untried_moves.remove(move)
        board.drop(move)
        child = _Node(board, move, node)
        node.children.append(child)
        return child

    def _rollout(self, board: Board, root_player: int) -> float:
        """Play to terminal; return 1.0/0.5/0.0 for root_player."""
        while not board.is_terminal():
            board.drop(self._rollout_move(board))
        winner = board.winner()
        if winner == root_player:
            return 1.0
        if winner == 0:
            return 0.5
        return 0.0

    def _rollout_move(self, board: Board) -> int:
        """Random move, or with light heuristic: win > block > random."""
        moves = board.legal_moves()
        if self.rollout == "light":
            current = board.current_player()
            # take immediate win
            for col in moves:
                row = self._landing_row(board, col)
                board.grid[row][col] = current
                wins = self._four_at(board, row, col, current)
                board.grid[row][col] = 0
                if wins:
                    return col
            # block opponent's immediate win
            opp = 3 - current
            for col in moves:
                row = self._landing_row(board, col)
                board.grid[row][col] = opp
                wins = self._four_at(board, row, col, opp)
                board.grid[row][col] = 0
                if wins:
                    return col
        return self.rng.choice(moves)

    def _landing_row(self, board: Board, col: int) -> int:
        for row in range(board.ROWS):
            if board.grid[row][col] == 0:
                return row
        return -1

    def _four_at(self, board: Board, row: int, col: int, player: int) -> bool:
        """Check if player has four in a row through (row, col)."""
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1
            for sign in (1, -1):
                r, c = row + sign * dr, col + sign * dc
                while 0 <= r < board.ROWS and 0 <= c < board.COLS and board.grid[r][c] == player:
                    count += 1
                    r += sign * dr
                    c += sign * dc
            if count >= 4:
                return True
        return False

    def _backpropagate(self, node: _Node | None, result: float, root_player: int) -> None:
        """Propagate result up the tree; wins credited to root_player perspective."""
        while node is not None:
            node.visits += 1
            # to_move is the player who is *choosing* at this node.
            # After drop, it is the opponent's turn => the mover was to_move's parent.
            # We want wins from root_player's perspective stored consistently.
            # Standard MCTS stores wins for the player who chose the move INTO this node,
            # i.e., the parent's to_move. We track from root_player view instead for clarity.
            if node.to_move != root_player:
                # This node is root_player's move: result directly benefits root_player
                node.wins += result
            else:
                # This node is opponent's move: flip for their perspective
                node.wins += 1.0 - result if result != 0.5 else 0.5
            node = node.parent
