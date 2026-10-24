"""experiments/run_all.py — Run all four experiment studies and save CSVs.

Studies
-------
1. Ablation      : Minimax → AB → AB+ordering → AB+ID → AB+TT (depth 3 vs Rookie)
2. Tournament    : Rookie vs Tactician vs Grandmaster vs Gambler (20 games each pair)
3. Depth vs Time : AlphaBeta at depths 1-7, measuring avg time/move
4. Weight Tuning : Compare default weights vs two alternative weight sets

Usage
-----
    python -m experiments.run_all [--quick]   # --quick uses 10 games instead of 20

Output: results/<study>_<timestamp>.csv  +  results/latest_<study>.csv
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import sys
import time
from datetime import datetime

from agents.alphabeta import AlphaBetaAgent
from agents.base import Agent
from agents.evaluation import WEIGHTS, evaluate
from agents.mcts import MCTSAgent
from agents.minimax import MinimaxAgent
from experiments.arena import MatchResult, play_match
from game.board import Board

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

_TS = datetime.now().strftime("%Y%m%d_%H%M%S")


# ── CSV helpers ────────────────────────────────────────────────────────────────

def _save(rows: list[dict], name: str) -> pathlib.Path:
    """Save rows to results/<name>_<timestamp>.csv and results/latest_<name>.csv."""
    if not rows:
        return RESULTS_DIR / f"{name}.csv"
    keys = list(rows[0].keys())
    ts_path     = RESULTS_DIR / f"{name}_{_TS}.csv"
    latest_path = RESULTS_DIR / f"latest_{name}.csv"
    for path in (ts_path, latest_path):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    print(f"  Saved → {latest_path.name}")
    return latest_path


def _banner(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Study 1: Ablation ──────────────────────────────────────────────────────────

def study_ablation(n_games: int) -> None:
    _banner("Study 1 — Ablation (depth 3 vs Rookie AB d=2)")
    opponent = AlphaBetaAgent(depth=2, use_ordering=True, weights=WEIGHTS, name="Rookie")
    agents: list[Agent] = [
        MinimaxAgent(depth=3, name="Minimax-d3"),
        AlphaBetaAgent(depth=3, use_ordering=False, weights=WEIGHTS, name="AB-d3"),
        AlphaBetaAgent(depth=3, use_ordering=True,  weights=WEIGHTS, name="AB-d3+ord"),
        AlphaBetaAgent(depth=3, use_ordering=True,  weights=WEIGHTS,
                       use_iterative_deepening=True, time_limit=1.0, name="AB-d3+ID"),
        AlphaBetaAgent(depth=3, use_ordering=True,  weights=WEIGHTS,
                       use_tt=True, name="AB-d3+TT"),
    ]
    rows = []
    for agent in agents:
        print(f"  {agent.name} vs {opponent.name} …", end=" ", flush=True)
        r = play_match(agent, opponent, n_games=n_games)
        print(f"win={r.win_rate_a:.0%}  draw={r.draw_rate:.0%}  {r.total_time_s:.1f}s")
        row = r.as_dict()
        row["study"] = "ablation"
        rows.append(row)
    _save(rows, "ablation")


# ── Study 2: Tournament ────────────────────────────────────────────────────────

def study_tournament(n_games: int) -> None:
    _banner("Study 2 — Tournament (all pairs)")
    agents: list[Agent] = [
        AlphaBetaAgent(depth=2, use_ordering=True, weights=WEIGHTS, name="Rookie"),
        AlphaBetaAgent(depth=5, use_ordering=True, weights=WEIGHTS, name="Tactician"),
        AlphaBetaAgent(depth=7, use_ordering=True, use_iterative_deepening=True,
                       time_limit=2.0, weights=WEIGHTS, name="Grandmaster"),
        MCTSAgent(simulations=500, seed=42, name="Gambler"),
    ]
    rows = []
    for i, a in enumerate(agents):
        for j, b in enumerate(agents):
            if j <= i:
                continue
            print(f"  {a.name} vs {b.name} …", end=" ", flush=True)
            r = play_match(a, b, n_games=n_games)
            print(f"{a.name}={r.win_rate_a:.0%}  {b.name}={r.win_rate_b:.0%}  "
                  f"draw={r.draw_rate:.0%}  {r.total_time_s:.1f}s")
            row = r.as_dict()
            row["study"] = "tournament"
            rows.append(row)
    _save(rows, "tournament")


# ── Study 3: Depth vs Time ────────────────────────────────────────────────────

def study_depth_vs_time() -> None:
    _banner("Study 3 — Depth vs Time (AlphaBeta, fixed opening position)")
    # Use a fixed mid-game position so depth differences are meaningful
    moves = [3, 3, 2, 4, 3, 2, 4, 2, 1, 5]
    board = Board()
    for col in moves:
        board.drop(col)

    rows = []
    for depth in range(1, 8):
        agent = AlphaBetaAgent(depth=depth, use_ordering=True, weights=WEIGHTS,
                               name=f"AB-d{depth}")
        times = []
        nodes_list = []
        for _ in range(5):          # 5 trials per depth on the same position
            b = board.copy()
            t0 = time.perf_counter()
            agent.choose_move(b)
            times.append(time.perf_counter() - t0)
            nodes_list.append(agent.last_stats.nodes)
        avg_t = sum(times) / len(times)
        avg_n = sum(nodes_list) / len(nodes_list)
        print(f"  depth={depth}  avg_time={avg_t:.4f}s  avg_nodes={avg_n:,.0f}")
        rows.append({
            "depth": depth,
            "avg_time_s": round(avg_t, 5),
            "avg_nodes": int(avg_n),
            "study": "depth_vs_time",
        })
    _save(rows, "depth_vs_time")


# ── Study 4: Weight Tuning ─────────────────────────────────────────────────────

def study_weight_tuning(n_games: int) -> None:
    _banner("Study 4 — Evaluation Weight Tuning")
    # Default vs two alternative weight sets, each played against Tactician
    opponent = AlphaBetaAgent(depth=5, use_ordering=True, weights=WEIGHTS, name="Tactician")

    alt_weights_list = [
        ("default",    WEIGHTS),
        ("aggressive", {**WEIGHTS, "three": WEIGHTS["three"] * 2,
                        "playable_three": WEIGHTS["playable_three"] * 2,
                        "center": WEIGHTS["center"] * 2}),
        ("defensive",  {**WEIGHTS, "opp_three": WEIGHTS["opp_three"] * 2,
                        "double_threat": WEIGHTS["double_threat"] * 2,
                        "center": WEIGHTS["center"] // 2}),
    ]
    rows = []
    for label, w in alt_weights_list:
        agent = AlphaBetaAgent(depth=3, use_ordering=True, weights=w,
                               name=f"AB-d3-{label}")
        print(f"  {agent.name} vs {opponent.name} …", end=" ", flush=True)
        r = play_match(agent, opponent, n_games=n_games)
        print(f"win={r.win_rate_a:.0%}  draw={r.draw_rate:.0%}  {r.total_time_s:.1f}s")
        row = r.as_dict()
        row["weight_set"] = label
        row["study"] = "weight_tuning"
        rows.append(row)
    _save(rows, "weight_tuning")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Run all Four-in-a-Row experiments.")
    parser.add_argument("--quick", action="store_true",
                        help="Use 3 games per match for fast smoke testing (NOTE: change back to 10 later)")
    parser.add_argument("--games", type=int, default=None,
                        help="Explicit number of games per match (overrides --quick)")
    parser.add_argument("--study", choices=["ablation", "tournament", "depth", "weights", "all"],
                        default="all", help="Which study to run (default: all)")
    args = parser.parse_args()

    # NOTE: Set to 3 for ultra-fast smoke testing; change back to 10 (or 20 for full runs) later
    if args.games is not None:
        n = args.games
    elif args.quick:
        n = 3  # NOTE: Temporary fast smoke test count (3 games). Revert to 10 when ready!
    else:
        n = 20
    print(f"Running with n_games={n} per match  |  results → {RESULTS_DIR}/")

    s = args.study
    if s in ("ablation", "all"):  study_ablation(n)
    if s in ("tournament", "all"): study_tournament(n)
    if s in ("depth", "all"):     study_depth_vs_time()
    if s in ("weights", "all"):   study_weight_tuning(n)

    print("\nDone. Run  python -m experiments.plot_results  to generate graphs.")


if __name__ == "__main__":
    main()
