"""Run the four experiments and save each one as a CSV in results/.

1. Ablation:      Minimax, then Alpha-Beta, + move ordering, + iterative deepening,
                  + transposition table (all depth 3) against Rookie (Alpha-Beta depth 2)
2. Tournament:    Rookie, Tactician, Grandmaster and Gambler play every pairing
3. Depth vs time: Alpha-Beta at depths 1-7 on one fixed mid-game position
4. Weight tuning: three evaluation weight sets against Tactician

Usage:  python -m experiments.run_all [--quick | --games N] [--study NAME]
Output: results/latest_<study>.csv (overwritten on every run)
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import time

from agents.alphabeta import AlphaBetaAgent
from agents.evaluation import WEIGHTS
from agents.mcts import MCTSAgent
from agents.minimax import MinimaxAgent
from experiments.arena import play_match
from game.board import Board

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"
OPENING_MOVES = 4  # each pair of games starts from its own random 4-move opening


def save(rows: list[dict], name: str) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / f"latest_{name}.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  saved results/latest_{name}.csv")


def matches(pairs: list, n_games: int, study: str, **extra) -> list[dict]:
    """Play each (agent, opponent) pair and return one CSV row per match."""
    rows = []
    for a, b in pairs:
        row = play_match(a, b, n_games=n_games, seed=42, openings=OPENING_MOVES).as_dict()
        print(f"  {a.name} vs {b.name}: {a.name} {row['win_rate_a']:.0%}, {b.name} {row['win_rate_b']:.0%}, "
              f"draws {row['draw_rate']:.0%}, {row['avg_nodes_a']:,} nodes/move, {row['total_time_s']:.1f}s")
        rows.append({**row, **extra.get(a.name, {}), "study": study})
    return rows


def study_ablation(n: int) -> None:
    print("\nStudy 1: ablation (depth 3 vs Rookie)")
    rookie = AlphaBetaAgent(depth=2, weights=WEIGHTS, name="Rookie")
    agents = [
        MinimaxAgent(depth=3, weights=WEIGHTS, name="Minimax-d3"),
        AlphaBetaAgent(depth=3, use_ordering=False, weights=WEIGHTS, name="AB-d3"),
        AlphaBetaAgent(depth=3, weights=WEIGHTS, name="AB-d3+ord"),
        AlphaBetaAgent(depth=3, weights=WEIGHTS, use_iterative_deepening=True, time_limit=1.0, name="AB-d3+ID"),
        AlphaBetaAgent(depth=3, weights=WEIGHTS, use_tt=True, name="AB-d3+TT"),
    ]
    save(matches([(a, rookie) for a in agents], n, "ablation"), "ablation")


def study_tournament(n: int) -> None:
    print("\nStudy 2: tournament (every pairing)")
    agents = [
        AlphaBetaAgent(depth=2, weights=WEIGHTS, name="Rookie"),
        AlphaBetaAgent(depth=5, weights=WEIGHTS, name="Tactician"),
        AlphaBetaAgent(depth=7, weights=WEIGHTS, use_iterative_deepening=True, time_limit=2.0, name="Grandmaster"),
        MCTSAgent(simulations=500, seed=42, name="Gambler"),
    ]
    pairs = [(a, b) for i, a in enumerate(agents) for b in agents[i + 1:]]
    save(matches(pairs, n, "tournament"), "tournament")


def study_depth_vs_time() -> None:
    print("\nStudy 3: depth vs time (Alpha-Beta, fixed position, 5 runs per depth)")
    board = Board()
    for col in (3, 3, 2, 4, 3, 2, 4, 2, 1, 5):  # same position as the app's fixed demo opening
        board.drop(col)
    rows = []
    for depth in range(1, 8):
        agent = AlphaBetaAgent(depth=depth, weights=WEIGHTS)
        start = time.perf_counter()
        for _ in range(5):
            agent.choose_move(board)
        avg_time = (time.perf_counter() - start) / 5
        print(f"  depth {depth}: {avg_time:.4f}s, {agent.last_stats.nodes:,} nodes")
        rows.append({"depth": depth, "avg_time_s": round(avg_time, 5),
                     "avg_nodes": agent.last_stats.nodes, "study": "depth_vs_time"})
    save(rows, "depth_vs_time")


def study_weight_tuning(n: int) -> None:
    print("\nStudy 4: evaluation weight tuning (depth 3 vs Tactician)")
    tactician = AlphaBetaAgent(depth=5, weights=WEIGHTS, name="Tactician")
    weight_sets = {
        "default": WEIGHTS,
        "aggressive": {**WEIGHTS, "three": WEIGHTS["three"] * 2,
                       "playable_three": WEIGHTS["playable_three"] * 2, "center": WEIGHTS["center"] * 2},
        # Note: evaluate() does not read "opp_three", so only the last two changes matter here.
        "defensive": {**WEIGHTS, "opp_three": WEIGHTS["opp_three"] * 2,
                      "double_threat": WEIGHTS["double_threat"] * 2, "center": WEIGHTS["center"] // 2},
    }
    agents = [AlphaBetaAgent(depth=3, weights=w, name=f"AB-d3-{label}") for label, w in weight_sets.items()]
    extra = {f"AB-d3-{label}": {"weight_set": label} for label in weight_sets}
    save(matches([(a, tactician) for a in agents], n, "weight_tuning", **extra), "weight_tuning")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Four-in-a-Row experiments.")
    parser.add_argument("--quick", action="store_true", help="10 games per match instead of 20")
    parser.add_argument("--games", type=int, help="games per match (overrides --quick)")
    parser.add_argument("--study", choices=["ablation", "tournament", "depth", "weights", "all"], default="all")
    args = parser.parse_args()
    n = args.games or (10 if args.quick else 20)
    print(f"{n} games per match, results go to {RESULTS_DIR}/")

    if args.study in ("ablation", "all"):
        study_ablation(n)
    if args.study in ("tournament", "all"):
        study_tournament(n)
    if args.study in ("depth", "all"):
        study_depth_vs_time()
    if args.study in ("weights", "all"):
        study_weight_tuning(n)
    print("\nDone. Run  python -m experiments.plot_results  to draw the graphs.")


if __name__ == "__main__":
    main()
