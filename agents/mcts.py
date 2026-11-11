"""Monte Carlo Tree Search (UCT): select, expand, simulate, backpropagate."""

from __future__ import annotations

import math
import random
from time import perf_counter

from agents.base import Agent, SearchStats
from config import MCTS_C
from game.board import Board


class _Node:
    __slots__ = ("move", "parent", "children", "untried", "visits", "wins", "to_move")

    def __init__(self, board: Board, move: int | None = None, parent: _Node | None = None) -> None:
        self.move = move  # column played to reach this node
        self.parent = parent
        self.children: list[_Node] = []
        self.untried = board.legal_moves()
        self.visits = 0
        self.wins = 0.0  # from the view of the player who made `move`
        self.to_move = board.current_player()

    def ucb1(self, c: float) -> float:
        if self.visits == 0:
            return math.inf
        return self.wins / self.visits + c * math.sqrt(math.log(self.parent.visits) / self.visits)


class MCTSAgent(Agent):
    def __init__(
        self,
        simulations: int = 2000,
        time_limit: float | None = None,
        c: float = MCTS_C,
        rollout: str = "random",  # "random" or "light" (win > block > random)
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
        start = perf_counter()
        self.last_stats = stats = SearchStats()
        me = board.current_player()

        win = next((c for c in board.legal_moves() if board.would_win(c, me)), None)
        if win is not None:
            stats.best_move = win
            return win

        root = _Node(board)
        sims = 0
        while (perf_counter() - start < self.time_limit) if self.time_limit else sims < self.simulations:
            b = board.copy()
            node = root
            # 1. Selection: follow the best UCB1 child while the node is fully expanded.
            while not node.untried and node.children:
                node = max(node.children, key=lambda n: n.ucb1(self.c))
                b.drop(node.move)
            # 2. Expansion: add one random untried move.
            if node.untried and not b.is_terminal():
                move = self.rng.choice(node.untried)
                node.untried.remove(move)
                b.drop(move)
                child = _Node(b, move, node)
                node.children.append(child)
                node = child
            # 3. Simulation: play to the end.
            while not b.is_terminal():
                b.drop(self._rollout_move(b))
            winner = b.winner()
            result = 0.5 if winner == 0 else float(winner == me)
            # 4. Backpropagation: credit each node from its mover's point of view.
            while node:
                node.visits += 1
                node.wins += result if node.to_move != me else 1.0 - result
                node = node.parent
            sims += 1
            if sims % 200 == 0 and self.on_progress:
                self.on_progress({"simulations": sims,
                                  "best_move": max(root.children, key=lambda n: n.visits).move})

        best = max(root.children, key=lambda n: n.visits)
        stats.simulations = sims
        stats.best_move = best.move
        stats.time_s = perf_counter() - start
        stats.column_scores = {n.move: n.wins / n.visits if n.visits else 0.0 for n in root.children}
        return best.move

    def _rollout_move(self, board: Board) -> int:
        moves = board.legal_moves()
        if self.rollout == "light":
            me = board.current_player()
            for player in (me, 3 - me):  # take a win, else block one
                for col in moves:
                    if board.would_win(col, player):
                        return col
        return self.rng.choice(moves)
