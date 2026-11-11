"""Play a series of games between two agents and collect the results."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from agents.base import Agent
from game.board import Board


@dataclass
class MatchResult:
    agent_a: str
    agent_b: str
    n_games: int
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0
    total_time_s: float = 0.0
    move_counts: list[int] = field(default_factory=list)
    nodes_a: int = 0   # positions searched by agent_a over all its moves
    moves_a: int = 0   # number of moves agent_a made

    @property
    def win_rate_a(self) -> float:
        return self.wins_a / self.n_games if self.n_games else 0.0

    @property
    def win_rate_b(self) -> float:
        return self.wins_b / self.n_games if self.n_games else 0.0

    @property
    def draw_rate(self) -> float:
        return self.draws / self.n_games if self.n_games else 0.0

    @property
    def avg_moves(self) -> float:
        return sum(self.move_counts) / len(self.move_counts) if self.move_counts else 0.0

    def as_dict(self) -> dict:
        return {
            "agent_a": self.agent_a, "agent_b": self.agent_b, "n_games": self.n_games,
            "wins_a": self.wins_a, "wins_b": self.wins_b, "draws": self.draws,
            "win_rate_a": round(self.win_rate_a, 4), "win_rate_b": round(self.win_rate_b, 4),
            "draw_rate": round(self.draw_rate, 4), "avg_moves": round(self.avg_moves, 2),
            "total_time_s": round(self.total_time_s, 3),
            "avg_nodes_a": round(self.nodes_a / self.moves_a) if self.moves_a else 0,
        }


def random_opening(rng: random.Random, length: int) -> list[int]:
    """`length` random moves that do not end the game."""
    while True:
        board = Board()
        for _ in range(length):
            board.drop(rng.choice(board.legal_moves()))
        if not board.is_terminal():
            return list(board.move_history)


def play_match(agent_a: Agent, agent_b: Agent, n_games: int = 20, seed: int = 0,
               verbose: bool = False, openings: int = 0) -> MatchResult:
    """Play `n_games` games, swapping who moves first every game so neither side
    gets the first-move advantage more often.

    Search agents are deterministic, so from an empty board they would replay the
    same two games over and over. With `openings > 0`, each pair of games starts
    from the same seeded random opening of that many moves, once with each agent
    moving first. Opening moves are not counted in `nodes_a`/`moves_a`.
    """
    rng = random.Random(seed)
    result = MatchResult(agent_a.name, agent_b.name, n_games)
    start = time.perf_counter()
    opening: list[int] = []
    for game in range(n_games):
        players = {1: agent_a, 2: agent_b} if game % 2 == 0 else {1: agent_b, 2: agent_a}
        if game % 2 == 0 and openings:
            opening = random_opening(rng, openings)
        board = Board()
        for col in opening:
            board.drop(col)
        while not board.is_terminal():
            agent = players[board.current_player()]
            board.drop(agent.choose_move(board))
            if agent is agent_a:
                result.nodes_a += agent.last_stats.nodes
                result.moves_a += 1
        result.move_counts.append(len(board.move_history))
        winner = board.winner()
        if winner == 0:
            result.draws += 1
        elif players[winner] is agent_a:
            result.wins_a += 1
        else:
            result.wins_b += 1
        if verbose:
            print(f"  game {game + 1}/{n_games}: {len(board.move_history)} moves, winner = player {winner}")
    result.total_time_s = time.perf_counter() - start
    return result
