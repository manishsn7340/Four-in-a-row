"""experiments/arena.py — Play a series of games between two agents.

Public API
----------
MatchResult   dataclass: wins/draws/losses, per-game timing, move counts
play_match    run n_games alternating who starts first; return MatchResult
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from agents.base import Agent
from game.board import Board


@dataclass
class MatchResult:
    """Aggregate results of a series of games between agent_a and agent_b."""
    agent_a: str
    agent_b: str
    n_games: int
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0
    total_time_s: float = 0.0
    move_counts: list[int] = field(default_factory=list)

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
            "agent_a": self.agent_a,
            "agent_b": self.agent_b,
            "n_games": self.n_games,
            "wins_a": self.wins_a,
            "wins_b": self.wins_b,
            "draws": self.draws,
            "win_rate_a": round(self.win_rate_a, 4),
            "win_rate_b": round(self.win_rate_b, 4),
            "draw_rate": round(self.draw_rate, 4),
            "avg_moves": round(self.avg_moves, 2),
            "total_time_s": round(self.total_time_s, 3),
        }


def play_match(
    agent_a: Agent,
    agent_b: Agent,
    n_games: int = 20,
    seed: int = 0,
    verbose: bool = False,
) -> MatchResult:
    """Run n_games games alternating who plays as P1 (first mover).

    For even-numbered games, agent_a is P1; for odd-numbered games, agent_b is P1.
    This gives each agent an equal number of first-mover advantages.

    The board is reset between games; agents are NOT re-created (stats accumulate).
    """
    result = MatchResult(
        agent_a=agent_a.name,
        agent_b=agent_b.name,
        n_games=n_games,
    )
    t_start = time.perf_counter()

    for game_idx in range(n_games):
        board = Board()
        # Alternate who is P1
        if game_idx % 2 == 0:
            p1, p2 = agent_a, agent_b
        else:
            p1, p2 = agent_b, agent_a

        moves = 0
        while not board.is_terminal():
            agent = p1 if board.current_player() == 1 else p2
            col = agent.choose_move(board)
            board.drop(col)
            moves += 1

        result.move_counts.append(moves)
        winner = board.winner()

        # Map board winner (1/2/0) back to agent_a/agent_b/draw
        if winner == 0:
            result.draws += 1
        elif (game_idx % 2 == 0 and winner == 1) or (game_idx % 2 == 1 and winner == 2):
            result.wins_a += 1          # agent_a won
        else:
            result.wins_b += 1          # agent_b won

        if verbose:
            winner_name = (
                "Draw" if winner == 0
                else (agent_a.name if result.wins_a > (result.wins_a - (1 if winner else 0)) else agent_b.name)
            )
            print(f"  Game {game_idx + 1:>3}/{n_games}: {moves} moves → winner={winner}")

    result.total_time_s = time.perf_counter() - t_start
    return result
